# Tests

Hardware-free regression tests for the Cervicheck interface. They replay
recorded Arduino transcripts, so no device needs to be connected.

## Running

```
cd Interface_Master/tests
../../.venv/bin/python test_communication.py
../../.venv/bin/python test_config.py
```

Both print a PASS/FAIL list and exit non-zero on failure. They also work under
pytest if you install it:

```
.venv/bin/python -m pytest Interface_Master/tests -q
```

## What each file covers

| File | Covers |
|---|---|
| `test_communication.py` | Line parsers, `pressureSweep`, `readCalibration`, `sendCalibration`, `applySweepSettings`, `calibCheck`, plus layering guards that fail if `communication.py` ever imports a GUI module again |
| `test_config.py` | Pad-count plumbing, dataframe row template, `reset()` round-trip |
| `capture.py` | Records new fixtures from real hardware |
| `fixtures/` | Recorded transcripts the tests replay |

## Re-recording fixtures

The golden values in `test_communication.py` are pinned to the current
fixtures. Different *measurements* between runs are fine and change nothing.
Re-record only if the firmware's output *format* changes — a renamed line, an
added CSV field, a different number of values after `Done!`.

```
cd Interface_Master/tests
../../.venv/bin/python capture.py            # prints usage and examples
```

`capture.py` warns before anything physical happens and gives you 3 seconds to
prepare (finger on the tubing tip for `calibrate`, tubing on the gel for
`sweep`). Close the GUI first — only one process can hold the serial port.
