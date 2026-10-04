"""Hardware-free tests for the serial protocol layer.

Replays captured Arduino transcripts from fixtures/ through a fake serial port.
Run with:
    cd ~/Documents/GitHub/Cervicheck && .venv/bin/python -m pytest Interface_Master/tests -q
or standalone:
    cd ~/Documents/GitHub/Cervicheck/Interface_Master/tests && ../../.venv/bin/python test_communication.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
APP = HERE.parent
FIXTURES = HERE / 'fixtures'
sys.path.insert(0, str(APP))

from communication import (  # noqa: E402
    parsePressureLine, parseContactLine, pressureSweep,
    readCalibration, sendCalibration, calibCheck, applySweepSettings,
)
from data_analysis import fit_calibration  # noqa: E402

SWEEP = 'capture_output.txt'
CALIBRATE = 'calibrate_output.txt'


class FakeSerial:
    """Replays raw bytes with pyserial-with-timeout semantics.

    readline() yields one line at a time including its CRLF, returns any final
    unterminated fragment on its own, then returns b'' forever the way a real
    port does when the read timeout expires.
    """

    def __init__(self, data=b'', timeout=5):
        self.timeout = timeout
        self.written = bytearray()
        self._queue = self._split(data)

    @staticmethod
    def _split(data):
        lines = []
        while data:
            idx = data.find(b'\n')
            if idx == -1:
                lines.append(data)
                break
            lines.append(data[:idx + 1])
            data = data[idx + 1:]
        return lines

    def readline(self):
        return self._queue.pop(0) if self._queue else b''

    def write(self, payload):
        self.written.extend(payload)
        return len(payload)

    def reset_input_buffer(self):
        pass

    def close(self):
        pass


def load(name):
    return (FIXTURES / name).read_bytes()


def replay(name):
    return FakeSerial(load(name))


def decode_lines(name):
    ser = replay(name)
    out = []
    while True:
        raw = ser.readline()
        if not raw:
            return out
        out.append(raw.decode('ascii', errors='replace'))


# --- FakeSerial fidelity -----------------------------------------------------

def test_fakeserial_yields_crlf_lines():
    ser = FakeSerial(b'one\r\ntwo\r\n')
    assert ser.readline() == b'one\r\n'
    assert ser.readline() == b'two\r\n'
    assert ser.readline() == b''


def test_fakeserial_returns_unterminated_tail_then_empty():
    ser = FakeSerial(b'done\r\nReleasing Valve: ')
    assert ser.readline() == b'done\r\n'
    assert ser.readline() == b'Releasing Valve: '
    assert ser.readline() == b''
    assert ser.readline() == b''


def test_fakeserial_records_writes():
    ser = FakeSerial()
    ser.write(b's')
    ser.write(b'-1\r')
    assert bytes(ser.written) == b's-1\r'


# --- parsers, synthetic ------------------------------------------------------

def test_parse_pressure_line_valid():
    assert parsePressureLine('PRESSURE,10705,-1.00,3.07,0\r\n') == (10705.0, -1.0, 3.07, 0)


def test_parse_contact_line_valid():
    assert parseContactLine('CONTACT,26540,0,-5.26,3.69\r\n') == (26540.0, 0, -5.26, 3.69)


def test_parsers_reject_wrong_field_count():
    assert parsePressureLine('PRESSURE,1,2,3\r\n') is None
    assert parsePressureLine('PRESSURE,1,2,3,4,5\r\n') is None
    assert parseContactLine('CONTACT,1,2,3\r\n') is None


def test_parsers_reject_non_numeric():
    assert parsePressureLine('PRESSURE,x,-1.00,3.07,0\r\n') is None
    assert parseContactLine('CONTACT,1,notapad,-5.26,3.69\r\n') is None


def test_parsers_reject_merged_lines():
    merged = 'PRESSURE,10705,-1.00,3.07,0Pad 1 has been contacted\r\n'
    assert parsePressureLine(merged) is None


def test_parse_pressure_line_tolerates_whitespace():
    assert parsePressureLine('  PRESSURE,10705,-1.00,3.07,0  ') == (10705.0, -1.0, 3.07, 0)


# --- sweep fixture -----------------------------------------------------------

def test_sweep_fixture_every_pressure_line_parses():
    lines = decode_lines(SWEEP)
    pressure_lines = [ln for ln in lines if ln.startswith('PRESSURE,')]
    assert len(pressure_lines) == 359
    assert all(parsePressureLine(ln) is not None for ln in pressure_lines)


def test_sweep_fixture_contact_pads():
    lines = decode_lines(SWEEP)
    contacts = [parseContactLine(ln) for ln in lines if ln.startswith('CONTACT,')]
    assert all(c is not None for c in contacts)
    assert [c[1] for c in contacts] == [0, 1, 2, 3, 5, 6, 7]


def test_sweep_fixture_pad_numbers_in_range():
    lines = decode_lines(SWEEP)
    pads = [parsePressureLine(ln)[3] for ln in lines if ln.startswith('PRESSURE,')]
    assert min(pads) >= 0
    assert max(pads) <= 7


def test_sweep_fixture_timestamps_are_monotonic():
    lines = decode_lines(SWEEP)
    stamps = [parsePressureLine(ln)[0] for ln in lines if ln.startswith('PRESSURE,')]
    assert stamps == sorted(stamps)


def test_sweep_fixture_ends_with_unterminated_fragment():
    ser = replay(SWEEP)
    last = None
    while True:
        raw = ser.readline()
        if not raw:
            break
        last = raw
    assert last == b'Releasing Valve: '


def test_sweep_fixture_result_block():
    lines = [ln.strip() for ln in decode_lines(SWEEP)]
    done = lines.index('Done!')
    values = [float(v) for v in lines[done + 1:done + 9]]
    assert values == [-5.26, -5.82, -8.58, -9.94, 0.00, -11.33, -14.09, -15.45]
    assert lines[done + 9].startswith('Time:')
    assert float(lines[done + 9][6:]) == 44010.0


def test_sweep_fixture_zero_entry_is_valid_data():
    lines = [ln.strip() for ln in decode_lines(SWEEP)]
    done = lines.index('Done!')
    values = [float(v) for v in lines[done + 1:done + 9]]
    assert len(values) == 8
    assert values[4] == 0.0


# --- calibration fixture -----------------------------------------------------

def test_calibrate_fixture_structure():
    lines = [ln.strip() for ln in decode_lines(CALIBRATE)]
    assert lines[0].startswith('Voltage')
    assert lines[-1].startswith('Done')
    v_idx = lines.index('Pressure:')
    voltages = [float(v) for v in lines[1:v_idx]]
    pressures = [float(p) for p in lines[v_idx + 1:-1]]
    assert voltages == [50, 250, 500, 750, 1000, 1250]
    assert len(pressures) == len(voltages) == 6


def test_calibrate_fixture_regression():
    import scipy.stats
    lines = [ln.strip() for ln in decode_lines(CALIBRATE)]
    v_idx = lines.index('Pressure:')
    voltages = [float(v) for v in lines[1:v_idx]]
    pressures = [float(p) for p in lines[v_idx + 1:-1]]
    result = scipy.stats.linregress(pressures, voltages)
    assert abs(result.slope - (-70.1978)) < 0.01
    assert abs(result.intercept - 268.7727) < 0.01
    assert result.rvalue ** 2 > 0.99


def test_calibrate_fixture_has_no_line_longer_than_timeout_gap():
    ser = replay(CALIBRATE)
    count = 0
    while ser.readline():
        count += 1
    assert count == 15


# --- pressureSweep against the real transcript ------------------------------

GOLDEN_PADS = [0.0, -5.26, -5.82, -8.58, -9.94, 0.00, -11.33, -14.09, -15.45]
GOLDEN_ELAPSED = 44010.0


def run_sweep(name=SWEEP):
    ser = replay(name)
    events = []
    pads, elapsed = pressureSweep(ser, events.append)
    return ser, events, pads, elapsed


def test_sweep_sends_the_start_byte():
    ser, _, _, _ = run_sweep()
    assert bytes(ser.written) == b's'


def test_sweep_returns_golden_pads():
    _, _, pads, _ = run_sweep()
    assert list(pads) == GOLDEN_PADS


def test_sweep_returns_golden_elapsed():
    _, _, _, elapsed = run_sweep()
    assert elapsed == GOLDEN_ELAPSED


def test_sweep_pads_length_matches_config():
    import config
    _, _, pads, _ = run_sweep()
    assert len(pads) == config.PAD_COUNT + 1


def test_sweep_emits_contacts_for_the_right_pads():
    _, events, _, _ = run_sweep()
    contacts = [e for e in events if e[0] == 'contact']
    assert [e[2] for e in contacts] == [0, 1, 2, 3, 5, 6, 7]


def test_sweep_emits_every_pressure_sample():
    _, events, _, _ = run_sweep()
    assert len([e for e in events if e[0] == 'pressure']) == 359


def test_sweep_does_not_emit_pressure_or_contact_as_log():
    _, events, _, _ = run_sweep()
    logs = [e[1] for e in events if e[0] == 'log']
    assert not any(ln.startswith('PRESSURE,') or ln.startswith('CONTACT,') for ln in logs)


def test_sweep_logs_the_human_readable_lines():
    _, events, _, _ = run_sweep()
    logs = ''.join(e[1] for e in events if e[0] == 'log')
    assert 'Pad 0 has been contacted' in logs
    assert 'Done!' in logs
    assert 'Time: 44010' in logs


def test_sweep_does_not_abort_on_good_transcript():
    _, events, _, _ = run_sweep()
    assert not [e for e in events if e[0] == 'aborted']


def test_sweep_aborts_on_silent_device():
    ser = FakeSerial(b'')
    events = []
    pads, elapsed = pressureSweep(ser, events.append)
    assert pads is None and elapsed is None
    assert [e[0] for e in events] == ['aborted']


def test_sweep_survives_truncated_transcript():
    truncated = load(SWEEP)[:5000]
    ser = FakeSerial(truncated)
    events = []
    pads, elapsed = pressureSweep(ser, events.append)
    assert pads is None and elapsed is None
    assert events[-1][0] == 'aborted'


def test_sweep_tolerates_gap_shorter_than_abort_threshold():
    data = load(SWEEP)
    ser = FakeSerial(data)
    original = ser._queue
    ser._queue = original[:10] + [b'', b''] + original[10:]
    events = []
    pads, elapsed = pressureSweep(ser, events.append)
    assert list(pads) == GOLDEN_PADS
    assert elapsed == GOLDEN_ELAPSED


def test_sweep_ignores_garbled_numeric_line_in_result_block():
    data = load(SWEEP).replace(b'\r\n-8.58\r\n', b'\r\n-8.\xce58\r\n', 1)
    ser = FakeSerial(data)
    pads, elapsed = pressureSweep(ser, lambda e: None)
    assert elapsed == GOLDEN_ELAPSED
    assert pads[3] == 0.0
    assert pads[1] == -5.26 and pads[8] == -15.45


# --- readCalibration / sendCalibration --------------------------------------

GOLDEN_VOLTAGES = [50.0, 250.0, 500.0, 750.0, 1000.0, 1250.0]
GOLDEN_PRESSURES = [3.07, 0.28, -3.14, -7.22, -10.06, -14.09]


def run_calibration(data=None):
    ser = FakeSerial(load(CALIBRATE) if data is None else data)
    events = []
    voltages, pressures = readCalibration(ser, events.append)
    return ser, events, voltages, pressures


def test_calibration_sends_the_start_byte():
    ser, _, _, _ = run_calibration()
    assert bytes(ser.written) == b'p'


def test_calibration_returns_golden_series():
    _, _, voltages, pressures = run_calibration()
    assert voltages == GOLDEN_VOLTAGES
    assert pressures == GOLDEN_PRESSURES


def test_calibration_headers_are_not_captured_as_data():
    _, _, voltages, pressures = run_calibration()
    assert len(voltages) == len(pressures) == 6


def test_calibration_logs_every_line():
    _, events, _, _ = run_calibration()
    logs = [e[1].strip() for e in events if e[0] == 'log']
    assert logs[0].startswith('Voltage')
    assert logs[-1].startswith('Done')
    assert len(logs) == 15


def test_calibration_feeds_the_known_regression():
    _, _, voltages, pressures = run_calibration()
    slope, intercept, r_squared = fit_calibration(pressures, voltages)
    assert abs(slope - (-70.1978)) < 0.01
    assert abs(intercept - 268.7727) < 0.01
    assert r_squared > 0.99


def test_calibration_aborts_on_silent_device():
    ser, events, voltages, pressures = run_calibration(b'')
    assert voltages is None and pressures is None
    assert [e[0] for e in events] == ['aborted']


def test_calibration_aborts_without_done():
    data = load(CALIBRATE).replace(b'Done!\r\n', b'')
    _, events, voltages, _ = run_calibration(data)
    assert voltages is None
    assert events[-1][0] == 'aborted'


def test_calibration_aborts_on_mismatched_series():
    data = load(CALIBRATE).replace(b'-14.09\r\n', b'', 1)
    _, events, voltages, _ = run_calibration(data)
    assert voltages is None
    assert events[-1][0] == 'aborted'


def test_calibration_tolerates_three_second_gaps():
    ser = FakeSerial(load(CALIBRATE))
    ser._queue = [ser._queue[0]] + [b''] + ser._queue[1:]
    events = []
    voltages, pressures = readCalibration(ser, events.append)
    assert voltages == GOLDEN_VOLTAGES
    assert pressures == GOLDEN_PRESSURES


def test_send_calibration_writes_r_then_two_values():
    ser = FakeSerial()
    sendCalibration(ser, -70.1978, 268.7727)
    assert bytes(ser.written) == b'r-70.1978\r268.7727\r'


# --- calibCheck --------------------------------------------------------------

CALIBCHECK_OK = (b'CALIBCHECK,Pad 0 Voltage: 4.80\r\n'
                 b'CALIBCHECK,Pad 1 Voltage: 4.77\r\n'
                 b'DONE\r\n')


def test_calibcheck_sends_command_and_reports_lines():
    ser = FakeSerial(CALIBCHECK_OK)
    events = []
    assert calibCheck(ser, events.append) is True
    assert bytes(ser.written) == b'c\r'
    assert [e[1].strip() for e in events] == [
        'CALIBCHECK,Pad 0 Voltage: 4.80', 'CALIBCHECK,Pad 1 Voltage: 4.77']


def test_calibcheck_does_not_log_the_done_sentinel():
    ser = FakeSerial(CALIBCHECK_OK)
    events = []
    calibCheck(ser, events.append)
    assert not any('DONE' in e[1] for e in events)


def test_calibcheck_aborts_on_silent_device():
    ser = FakeSerial(b'')
    events = []
    assert calibCheck(ser, events.append) is False
    assert [e[0] for e in events] == ['aborted']


def test_calibcheck_aborts_when_done_never_arrives():
    ser = FakeSerial(b'CALIBCHECK,Pad 0 Voltage: 4.80\r\n')
    events = []
    assert calibCheck(ser, events.append) is False
    assert events[-1][0] == 'aborted'


# --- applySweepSettings ------------------------------------------------------

ACCEPTED = b'Contact voltage threshold (V): 2.00\r\n'
REJECTED = (b'Ignored out-of-range contact threshold: 500.00\r\n'
            b'Contact voltage threshold (V): 4.50\r\n')


def apply_settings(reply, values=('-1', '-1', '20', '2.0')):
    ser = FakeSerial(reply)
    accepted, rejected = applySweepSettings(ser, *values)
    return ser, accepted, rejected


def test_apply_settings_writes_i_then_four_values():
    ser, _, _ = apply_settings(ACCEPTED)
    assert bytes(ser.written) == b'i-1\r-1\r20\r2.0\r'


def test_apply_settings_accepts_confirmed_threshold():
    _, accepted, rejected = apply_settings(ACCEPTED)
    assert accepted == '2.00'
    assert rejected is None


def test_apply_settings_reports_rejected_threshold():
    _, accepted, rejected = apply_settings(REJECTED, ('-1', '-1', '20', '500'))
    assert rejected == '500.00'
    assert accepted == '4.50'


def test_apply_settings_reports_no_confirmation_when_silent():
    _, accepted, rejected = apply_settings(b'')
    assert accepted is None
    assert rejected is None


def test_apply_settings_accepts_boundary_value():
    _, accepted, rejected = apply_settings(b'Contact voltage threshold (V): 5.00\r\n',
                                           ('-1', '-1', '20', '5.0'))
    assert accepted == '5.00'
    assert rejected is None


def test_apply_settings_skips_stale_leftover_line():
    reply = b'Releasing Valve: \r\nContact voltage threshold (V): 3.25\r\n'
    _, accepted, rejected = apply_settings(reply)
    assert accepted == '3.25'


def test_apply_settings_skips_noise_before_confirmation():
    reply = b'garbage line\r\nContact voltage threshold (V): 4.50\r\n'
    _, accepted, _ = apply_settings(reply)
    assert accepted == '4.50'


def test_apply_settings_gives_up_after_four_reads():
    reply = b'noise\r\n' * 10
    _, accepted, _ = apply_settings(reply)
    assert accepted is None


def test_apply_settings_coerces_numeric_values():
    ser = FakeSerial(ACCEPTED)
    applySweepSettings(ser, -1, -1, 20, 2.0)
    assert bytes(ser.written) == b'i-1\r-1\r20\r2.0\r'


# --- layering guards ---------------------------------------------------------

FORBIDDEN_IN_PROTOCOL = {'tkinter', 'matplotlib', 'cv2', 'PIL', 'gui',
                         'ScrollableNotebook', 'Master', 'scipy'}


def module_imports(filename):
    import ast
    tree = ast.parse((APP / filename).read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split('.')[0])
    return found


def test_communication_imports_nothing_gui():
    leaked = module_imports('communication.py') & FORBIDDEN_IN_PROTOCOL
    assert not leaked, f"communication.py must not import {sorted(leaked)}"


def test_communication_does_not_import_gui_module():
    assert 'gui' not in module_imports('communication.py')


def test_data_analysis_imports_nothing_gui():
    leaked = module_imports('data_analysis.py') & (FORBIDDEN_IN_PROTOCOL - {'scipy'})
    assert not leaked, f"data_analysis.py must not import {sorted(leaked)}"


def test_config_imports_nothing_gui():
    leaked = module_imports('config.py') & FORBIDDEN_IN_PROTOCOL
    assert not leaked, f"config.py must not import {sorted(leaked)}"


def test_dependency_graph_is_acyclic():
    project = {'gui', 'communication', 'config', 'data_analysis', 'Master'}
    graph = {name: module_imports(f'{name}.py') & project for name in project}
    seen, stack = set(), set()

    def visit(node, path):
        if node in stack:
            raise AssertionError(f"import cycle: {' -> '.join(path + [node])}")
        if node in seen:
            return
        stack.add(node)
        seen.add(node)
        for dep in sorted(graph.get(node, ())):
            visit(dep, path + [node])
        stack.discard(node)

    for name in sorted(project):
        visit(name, [])


def test_communication_has_no_unused_imports():
    import ast
    tree = ast.parse((APP / 'communication.py').read_text())
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported[(alias.asname or alias.name).split('.')[0]] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported[alias.asname or alias.name] = alias.name
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.value.id for n in ast.walk(tree)
             if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    dead = sorted(k for k in imported if k not in used)
    assert not dead, f"unused imports in communication.py: {dead}"


if __name__ == '__main__':
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_')]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
