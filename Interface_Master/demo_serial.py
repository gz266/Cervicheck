"""Stand-in for serial.Serial so the GUI can run without the device.

Answers the same single-byte commands as the firmware by replaying the
transcripts recorded from real hardware in tests/fixtures/. Used by
`python Master.py --demo`.
"""

from pathlib import Path
from time import sleep

FIXTURES = Path(__file__).parent / 'tests' / 'fixtures'

# Seconds to wait before handing back each line, so the live plot animates
# instead of the whole sweep arriving at once.
LINE_DELAY = {'s': 0.02, 'p': 0.3, 'c': 0.05}

# Number of '\r'-terminated values that follow each command byte.
COMMAND_ARGS = {'i': 4, 'r': 2, 't': 1}


class DemoSerial:
    def __init__(self):
        self.timeout = 5
        self._queue = []
        self._delay = 0
        self._command = None
        self._args = []
        self._partial = ''

    def _respond(self, lines, delay=0):
        self._queue.extend(lines)
        self._delay = delay

    def _replay(self, fixture, command):
        data = (FIXTURES / fixture).read_bytes()
        self._respond(data.splitlines(keepends=True), LINE_DELAY[command])

    def _finishCommand(self):
        if self._command == 'i':
            try:
                thresh = float(self._args[3])
            except ValueError:
                thresh = 0.0
            if 0 < thresh <= 5.0:
                self._respond([f"Contact voltage threshold (V): {thresh:.2f}\r\n".encode()])
            else:
                self._respond([f"Ignored out-of-range contact threshold: {thresh:.2f}\r\n".encode(),
                               b"Contact voltage threshold (V): 4.50\r\n"])
        self._command = None
        self._args = []

    def write(self, payload):
        for char in payload.decode('ascii', errors='replace'):
            if self._command is not None:
                # Collecting the '\r'-terminated values that follow a command byte.
                if char == '\r':
                    self._args.append(self._partial)
                    self._partial = ''
                    if len(self._args) == COMMAND_ARGS[self._command]:
                        self._finishCommand()
                else:
                    self._partial += char
            elif char == 's':
                self._replay('capture_output.txt', 's')
            elif char == 'p':
                self._replay('calibrate_output.txt', 'p')
            elif char == 'c':
                lines = [f"CALIBCHECK,Pad {pad} Voltage: 5.00\r\n".encode() for pad in range(8)]
                self._respond(lines + [b"DONE\r\n"], LINE_DELAY['c'])
            elif char in COMMAND_ARGS:
                self._command = char
        return len(payload)

    def readline(self):
        if not self._queue:
            return b''
        sleep(self._delay)
        return self._queue.pop(0)

    def reset_input_buffer(self):
        self._queue.clear()

    def close(self):
        pass
