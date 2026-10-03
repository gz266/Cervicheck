from time import sleep
import numpy as np
import config


def parsePressureLine(data):
    parts = data.strip().split(',')
    if len(parts) != 5:
        return None

    try:
        return float(parts[1]), float(parts[2]), float(parts[3]), int(parts[4])
    except ValueError:
        return None


def parseContactLine(data):
    parts = data.strip().split(',')
    if len(parts) != 5:
        return None

    try:
        return float(parts[1]), int(parts[2]), float(parts[3]), float(parts[4])
    except ValueError:
        return None


def readCalibration(ser, on_event):
    ser.write(b'p')
    voltages = []
    pressures = []
    reading_voltage = False
    reading_pressure = False
    index = 0
    empty_reads = 0
    completed = False
    while empty_reads < 3:
        data = ser.readline().decode('ascii', errors='replace')
        if not data.strip():
            empty_reads += 1
            continue
        empty_reads = 0
        on_event(('log', data))
        if data.startswith("Done"):
            completed = True
            break
        if data.startswith("Voltage"):
            reading_voltage = True
            reading_pressure = False
            index = 0
        if data.startswith("Pressure"):
            reading_voltage = False
            reading_pressure = True
            index = 0
        target = voltages if reading_voltage else pressures if reading_pressure else None
        if target is not None:
            if index == 0:
                index += 1
            else:
                index += 1
                try:
                    target.append(float(data))
                except ValueError:
                    pass
    if not completed or len(voltages) != len(pressures) or len(pressures) < 2:
        on_event(('aborted', 'incomplete calibration data from device'))
        return None, None
    return voltages, pressures


def sendCalibration(ser, slope, intercept):
    ser.write(b'r')
    ser.write((str(slope) + '\r').encode())
    sleep(0.1)
    ser.write((str(intercept) + '\r').encode())
    sleep(0.1)


def pressureSweep(ser, on_event):
    ser.write(b's')
    pads = np.zeros(config.PAD_COUNT + 1)
    collecting = False
    index = 0
    empty_reads = 0
    while empty_reads < 3:
        data = ser.readline().decode('ascii', errors='replace')
        if not data.strip():
            empty_reads += 1
            continue
        empty_reads = 0
        if data.startswith("PRESSURE,"):
            parsed = parsePressureLine(data)
            if parsed is not None:
                on_event(('pressure',) + parsed)
            continue
        if data.startswith("CONTACT,"):
            parsed = parseContactLine(data)
            if parsed is not None:
                on_event(('contact',) + parsed)
            continue
        on_event(('log', data))
        if data.startswith("Done"):
            collecting = True
            index = 0
        if data.startswith("Time"):
            return pads, float(data[6:])
        if collecting:
            if index == 0:
                index += 1
            else:
                try:
                    pads[index] = float(data)
                except (ValueError, IndexError):
                    pass
                index += 1
    on_event(('aborted', 'no response from device'))
    return None, None


def applySweepSettings(ser, pres_start, pres_incr, pres_num_incr, volt_thresh):
    ser.write(b'i')
    for value in (pres_start, pres_incr, pres_num_incr, volt_thresh):
        ser.write((str(value) + '\r').encode())
        sleep(0.1)

    accepted = None
    rejected = None
    for _ in range(4):
        line = ser.readline().decode('ascii', errors='replace').strip()
        if not line:
            break
        if line.startswith("Ignored out-of-range contact threshold:"):
            rejected = line.split(':', 1)[1].strip()
        elif line.startswith("Contact voltage threshold"):
            accepted = line.split(':', 1)[1].strip()
            break
    return accepted, rejected


def calibCheck(ser, on_event):
    ser.write(b'c\r')
    empty_reads = 0
    while empty_reads < 2:
        data = ser.readline().decode('ascii', errors='replace')
        if not data.strip():
            empty_reads += 1
            continue
        empty_reads = 0
        if data.startswith("DONE"):
            return True
        on_event(('log', data))
    on_event(('aborted', 'no response from device'))
    return False

        
