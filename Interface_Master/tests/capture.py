"""Record raw Arduino serial output to a fixture file for replay in tests.

Examples:
    python capture.py calibcheck_run --command calibcheck
    python capture.py calib_run --command calibrate
    python capture.py settings_rejected --command settings --settings -1 -1 20 500
    python capture.py sweep_good --pre-calibration -79.24 44.45 --pre-settings -1 -1 20 4.5

Opening the port resets the Arduino, so every run starts from compile-time
defaults. --pre-calibration and --pre-settings replay your real parameters
first, in the same open-port session, so the fixture matches a real run.

Fixtures are written as raw bytes so line endings and unterminated partial
lines survive exactly as the Arduino sent them.
"""

import argparse
import sys
import time
from pathlib import Path

import serial
from serial.tools import list_ports

COMMANDS = {
    'sweep': {
        'byte': b's',
        'action': 'RUNS A FULL PRESSURE TEST',
        'prepare': 'Place the tubing against the gel / tissue.',
        'expect': '~7 s of preconditioning pulses, then pressure increments reading all 8 pads. '
                  'Ends by releasing the valve for 5 s.',
        'physical': True,
    },
    'calibrate': {
        'byte': b'p',
        'action': 'APPLIES AND HOLDS VACUUM',
        'prepare': 'Seal the tubing tip with your finger and hold it.',
        'expect': '6 vacuum levels, 3 s each (~18 s). Without a seal the readings are meaningless. '
                  'Pressure is released automatically at the end.',
        'physical': True,
    },
    'calibcheck': {
        'byte': b'c',
        'action': 'READS THE 8 PAD VOLTAGES',
        'prepare': 'No pressure is applied. Position the pads however you want them measured.',
        'expect': 'Under a second. Purely electrical.',
        'physical': True,
    },
    'settings': {
        'byte': b'i',
        'action': 'SETS PARAMETERS ONLY',
        'prepare': 'No hardware action. Nothing to prepare.',
        'expect': 'Instant. Echoes the accepted contact voltage threshold.',
        'physical': False,
    },
}


LIKELY_DEVICE = ('usbmodem', 'usbserial', 'ttyacm', 'ttyusb', 'wchusb', 'slab_usbto')


def pick_port(requested):
    if requested:
        return requested
    ports = list(list_ports.comports())
    if not ports:
        sys.exit("No serial ports found. Is the Arduino plugged in?")
    candidates = [p for p in ports
                  if any(tag in p.device.lower() for tag in LIKELY_DEVICE)] or ports
    if len(candidates) == 1:
        print(f"Using {candidates[0].device} ({candidates[0].description})")
        return candidates[0].device
    print("Available ports:")
    for idx, p in enumerate(candidates):
        print(f"  [{idx}] {p.device}  {p.description}")
    while True:
        choice = input("Port number: ").strip()
        if choice.isdigit() and int(choice) < len(candidates):
            return candidates[int(choice)].device
        print("Not a valid choice.")


def send_command(ser, byte, values=(), gap=0.1):
    ser.write(byte)
    for value in values:
        time.sleep(gap)
        ser.write((str(value) + '\r').encode())
    time.sleep(gap)


def drain(ser, label, reads=4, timeout=0.3):
    original = ser.timeout
    ser.timeout = timeout
    try:
        for _ in range(reads):
            line = ser.readline()
            if line:
                print(f"   [{label}] {line.decode('ascii', errors='replace').rstrip()}")
    finally:
        ser.timeout = original


def banner(text):
    line = '=' * 68
    print(f"\n{line}\n{text}\n{line}")


def countdown(seconds):
    for remaining in range(seconds, 0, -1):
        print(f"   starting in {remaining}...", flush=True)
        time.sleep(1)
    print("   GO\n", flush=True)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('name', help="fixture name, written as <outdir>/<name>.txt")
    ap.add_argument('--command', default='sweep', choices=sorted(COMMANDS),
                    help="which Arduino command to trigger (default: sweep)")
    ap.add_argument('--settings', nargs=4, metavar=('START', 'INCR', 'NUM', 'VOLTS'),
                    help="four values sent after the 'i' command")
    ap.add_argument('--port', help="serial port (auto-detected if omitted)")
    ap.add_argument('--baud', type=int, default=9600)
    ap.add_argument('--timeout', type=float, default=5.0)
    ap.add_argument('--silence', type=int, default=3,
                    help="stop after this many consecutive read timeouts (default: 3)")
    ap.add_argument('--max-seconds', type=float, default=600.0)
    ap.add_argument('--countdown', type=int, default=3,
                    help="seconds to prepare before the command is sent (default: 3, 0 to skip)")
    ap.add_argument('--pre-calibration', nargs=2, metavar=('SLOPE', 'YINT'),
                    help="send 'r' with these before the main command, undoing the reset "
                         "to the hardcoded -79.24 / 44.45")
    ap.add_argument('--pre-settings', nargs=4, metavar=('START', 'INCR', 'NUM', 'VOLTS'),
                    help="send 'i' with these before the main command, so the capture uses "
                         "your real sweep parameters instead of the 30-increment defaults")
    ap.add_argument('--outdir', default=str(Path(__file__).parent / 'fixtures'))
    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit(0)

    args = ap.parse_args()

    if args.command == 'settings' and not args.settings:
        ap.error("--command settings requires --settings START INCR NUM VOLTS")

    outdir = Path(args.outdir)
    outfile = outdir / f"{args.name}.txt"
    if outfile.exists():
        if input(f"{outfile} exists. Overwrite? [y/N] ").strip().lower() != 'y':
            sys.exit("Aborted.")

    spec = COMMANDS[args.command]
    port = pick_port(args.port)

    banner(f"OPENING PORT -- THIS RESETS THE ARDUINO\n"
           f"  All firmware settings revert to compile-time defaults:\n"
           f"  30 increments, threshold 4.5 V, slope -79.24, yint 44.45.\n"
           f"  Any calibration done through the GUI is lost.")
    ser = serial.Serial(port, baudrate=args.baud, timeout=args.timeout)
    print(f"Opened {port} at {args.baud} baud. Waiting 2 s for reset...")
    time.sleep(2)
    ser.reset_input_buffer()

    if args.pre_calibration:
        print(f"\nPre-sending calibration: slope={args.pre_calibration[0]} "
              f"yint={args.pre_calibration[1]}")
        send_command(ser, b'r', args.pre_calibration)
        drain(ser, 'r')

    if args.pre_settings:
        print(f"\nPre-sending settings: start={args.pre_settings[0]} "
              f"incr={args.pre_settings[1]} num={args.pre_settings[2]} "
              f"volts={args.pre_settings[3]}")
        send_command(ser, b'i', args.pre_settings)
        drain(ser, 'i')

    ser.reset_input_buffer()

    banner(f"NEXT: {args.command.upper()} -- {spec['action']}\n"
           f"  PREPARE: {spec['prepare']}\n"
           f"  EXPECT:  {spec['expect']}")
    if spec['physical'] and args.countdown > 0:
        countdown(args.countdown)

    send_command(ser, spec['byte'], args.settings or ())
    print(f"Sent {args.command!r}. Recording until {args.silence} consecutive "
          f"{args.timeout}s timeouts, or Ctrl-C.\n")

    captured = bytearray()
    lines = 0
    empties = 0
    started = time.monotonic()
    try:
        while empties < args.silence:
            if time.monotonic() - started > args.max_seconds:
                print(f"\n[max-seconds {args.max_seconds} reached]")
                break
            chunk = ser.readline()
            if not chunk:
                empties += 1
                print(f"[silence {empties}/{args.silence}]")
                continue
            empties = 0
            captured.extend(chunk)
            lines += 1
            sys.stdout.write(chunk.decode('ascii', errors='replace'))
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n[interrupted, saving what was captured]")
    finally:
        ser.close()

    if not captured:
        sys.exit("Nothing captured. Fixture not written.")

    outdir.mkdir(parents=True, exist_ok=True)
    outfile.write_bytes(bytes(captured))
    print(f"\nWrote {len(captured)} bytes / {lines} lines -> {outfile}")


if __name__ == '__main__':
    main()
