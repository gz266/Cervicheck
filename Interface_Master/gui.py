import pandas as pd
import cv2
from PIL import Image, ImageDraw
import threading
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import numpy as np
from PyQt6.QtCore import QObject, Qt, QTimer, QRectF, QLocale, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap, QDoubleValidator, QTextCursor
from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QGridLayout, QInputDialog, QSizePolicy
import communication
import config
from data_analysis import align_data, analyze_data, func, fit_calibration, predict_trimester


class _Dispatcher(QObject):
    """Runs functions on the GUI thread. Qt widgets may only be touched from the
    thread that created them, so the sweep/calibration threads hand their UI
    updates to this object through a queued signal (the Qt version of after(0))."""
    call = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.call.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @pyqtSlot(object)
    def _run(self, fn):
        try:
            fn()
        except RuntimeError as e:
            # The window was closed while a worker thread was still sending updates.
            if 'has been deleted' not in str(e):
                raise


# Created at import, which happens on the main thread, so it lives there.
_dispatcher = _Dispatcher()


def _ui(fn):
    _dispatcher.call.emit(fn)


class SweepCounter:
    """Number of the next sweep. Replaces tk.IntVar; same get()/set() interface."""
    def __init__(self, value=1):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


def setButtonAction(btn, text, action):
    """Point a button at a new action (the Qt version of btn.config(text=, command=))."""
    btn.setText(text)
    try:
        btn.clicked.disconnect()
    except TypeError:
        pass  # nothing was connected
    btn.clicked.connect(action)


def makeNumberValidator(parent):
    validator = QDoubleValidator(parent)
    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
    # Always use '.' as the decimal point, whatever the system locale.
    validator.setLocale(QLocale.c())
    return validator


PAD_CONTACT_COLOR = (46, 204, 113)


def loadFlexPcbImage():
    if os.path.exists(config.FLEX_PCB_IMAGE):
        return Image.open(config.FLEX_PCB_IMAGE).convert('RGBA')
    return drawPlaceholderFlexPcb()


def drawPlaceholderFlexPcb(width=800, height=200):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Polyimide flex strip
    draw.rounded_rectangle((10, 40, width - 10, height - 40), radius=30,
                           fill=(214, 140, 40), outline=(120, 70, 10), width=3)
    for x_frac, y_frac, r_frac in config.PAD_POSITIONS:
        cx, cy, r = x_frac * width, y_frac * height, r_frac * width
        # Trace from the pad to the edge of the strip
        draw.line((cx, cy, cx, height - 40), fill=(170, 110, 30), width=4)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r),
                     fill=(200, 200, 200), outline=(90, 90, 90), width=2)
    return img


def pilToPixmap(img):
    img = img.convert('RGBA')
    data = img.tobytes('raw', 'RGBA')
    qimg = QImage(data, img.width, img.height, 4 * img.width, QImage.Format.Format_RGBA8888)
    # copy() so the QImage owns its pixels instead of pointing into `data`.
    return QPixmap.fromImage(qimg.copy())


class PadIndicator(QWidget):
    """Picture of the flex PCB with the pads that have made contact lit up.
    Repaints itself on resize so the picture always fits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.contacted = set()
        self.base_pixmap = pilToPixmap(loadFlexPcbImage())
        self.setMinimumHeight(160)

    def clear(self):
        self.contacted.clear()
        self.update()

    def markContactUpTo(self, pad_num):
        # The firmware reports only the furthest pad when several make contact
        # in the same pressure step, and it walks pads front to back, stopping
        # at the first one not in contact. So every pad after the last reported
        # contact, up to this one, is touching too.
        first_new_pad = max(self.contacted, default=-1) + 1
        self.contacted.update(range(first_new_pad, pad_num + 1))
        self.update()

    def paintEvent(self, event):
        base = self.base_pixmap
        if base.isNull() or self.width() < 1 or self.height() < 1:
            return

        # Fit the picture inside the widget without stretching it.
        scale = min(self.width() / base.width(), self.height() / base.height())
        w = base.width() * scale
        h = base.height() * scale
        x0 = (self.width() - w) / 2
        y0 = (self.height() - h) / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(QRectF(x0, y0, w, h), base, QRectF(base.rect()))

        painter.setPen(Qt.PenStyle.NoPen)
        for pad in self.contacted:
            if not 0 <= pad < len(config.PAD_POSITIONS):
                continue
            x_frac, y_frac, r_frac = config.PAD_POSITIONS[pad]
            cx, cy, r = x0 + x_frac * w, y0 + y_frac * h, r_frac * w
            glow = r * 1.4
            painter.setBrush(QColor(*PAD_CONTACT_COLOR, 90))
            painter.drawEllipse(QRectF(cx - glow, cy - glow, 2 * glow, 2 * glow))
            painter.setBrush(QColor(*PAD_CONTACT_COLOR, 230))
            painter.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))

        painter.setPen(QColor(Qt.GlobalColor.black))
        for pad, (x_frac, y_frac, _) in enumerate(config.PAD_POSITIONS):
            cx, cy = x0 + x_frac * w, y0 + y_frac * h
            painter.drawText(QRectF(cx - 20, cy - 10, 40, 20), Qt.AlignmentFlag.AlignCenter, str(pad))
        painter.end()


def setupPadIndicator(parent=None):
    return PadIndicator(parent)


def setupLivePressurePlot(live_plot_holder):
    if live_plot_holder is None:
        return

    parent = live_plot_holder.get('parent')
    if parent is None:
        return

    # Swap out the previous sweep's plot.
    old_canvas = live_plot_holder.get('plot_canvas')
    if old_canvas is not None:
        parent.layout().removeWidget(old_canvas)
        old_canvas.deleteLater()

    fig = Figure(figsize=(3, 2), layout='constrained')
    ax = fig.add_subplot()
    actual_line, = ax.plot([], [], 'b-', label='Measured')
    target_line, = ax.plot([], [], 'r--', label='Target')

    ax.set_title("Live Pressure")
    ax.set_ylabel("Pressure (kPa)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, linestyle='--', linewidth=0.5)
    ax.legend(loc='best')

    plot_canvas = FigureCanvasQTAgg(fig)
    parent.layout().addWidget(plot_canvas)

    live_plot_holder.update({
        'fig': fig,
        'ax': ax,
        'plot_canvas': plot_canvas,
        'actual_line': actual_line,
        'target_line': target_line,
        'times': [],
        'actual_pressures': [],
        'target_pressures': [],
        'pads': [],
        'start_time_ms': None,
        'contact_artists': []
    })

    status = live_plot_holder.get('status')
    if status is not None:
        status.setText("Live pressure: waiting for samples")

    pad_indicator = live_plot_holder.get('pad_indicator')
    if pad_indicator is not None:
        pad_indicator.clear()


def updateLivePressurePlot(live_plot_holder, time_ms, target_pressure, actual_pressure, pad_num):
    if live_plot_holder is None or live_plot_holder.get('plot_canvas') is None:
        return

    if live_plot_holder.get('start_time_ms') is None:
        live_plot_holder['start_time_ms'] = time_ms

    elapsed_s = (time_ms - live_plot_holder['start_time_ms']) / 1000.0
    live_plot_holder['times'].append(elapsed_s)
    live_plot_holder['target_pressures'].append(target_pressure)
    live_plot_holder['actual_pressures'].append(actual_pressure)
    live_plot_holder['pads'].append(pad_num)

    plot_canvas = live_plot_holder['plot_canvas']

    def apply():
        times = live_plot_holder['times']
        actual_pressures = live_plot_holder['actual_pressures']
        target_pressures = live_plot_holder['target_pressures']
        if not times:
            return

        live_plot_holder['actual_line'].set_data(times, actual_pressures)
        live_plot_holder['target_line'].set_data(times, target_pressures)

        all_pressures = actual_pressures + target_pressures
        pressure_min = min(all_pressures)
        pressure_max = max(all_pressures)
        pressure_pad = max(1.0, (pressure_max - pressure_min) * 0.15)

        ax = live_plot_holder['ax']
        ax.set_xlim(0, max(1.0, times[-1]))
        ax.set_ylim(pressure_min - pressure_pad, pressure_max + pressure_pad)

        status = live_plot_holder.get('status')
        if status is not None:
            status.setText(f"Pad {pad_num} | Target {target_pressure:.2f} kPa | Measured {actual_pressure:.2f} kPa")

        plot_canvas.draw_idle()

    _ui(apply)


def markPressureContact(live_plot_holder, time_ms, pad_num, pressure, voltage):
    if live_plot_holder is None or live_plot_holder.get('plot_canvas') is None:
        return

    start_time_ms = live_plot_holder.get('start_time_ms')
    elapsed_s = 0 if start_time_ms is None else (time_ms - start_time_ms) / 1000.0

    plot_canvas = live_plot_holder['plot_canvas']

    def apply():
        marker_time = elapsed_s
        marker_pressure = pressure
        times = live_plot_holder.get('times', [])
        actual_pressures = live_plot_holder.get('actual_pressures', [])
        target_pressures = live_plot_holder.get('target_pressures', [])

        if times and actual_pressures:
            nearest_index = min(range(len(times)), key=lambda idx: abs(times[idx] - elapsed_s))
            marker_time = times[nearest_index]
            marker_pressure = actual_pressures[nearest_index]

        ax = live_plot_holder['ax']
        marker = ax.scatter([marker_time], [marker_pressure], s=35, c='black', zorder=5)
        live_plot_holder['contact_artists'].append(marker)

        all_times = times + [marker_time]
        all_pressures = actual_pressures + target_pressures + [marker_pressure]
        if all_times:
            ax.set_xlim(0, max(1.0, max(all_times)))
        if all_pressures:
            pressure_min = min(all_pressures)
            pressure_max = max(all_pressures)
            pressure_pad = max(1.0, (pressure_max - pressure_min) * 0.15)
            ax.set_ylim(pressure_min - pressure_pad, pressure_max + pressure_pad)

        status = live_plot_holder.get('status')
        if status is not None:
            status.setText(f"Pad {pad_num} contact | Pressure {pressure:.2f} kPa | Voltage {voltage:.2f} V")

        pad_indicator = live_plot_holder.get('pad_indicator')
        if pad_indicator is not None:
            pad_indicator.markContactUpTo(pad_num)

        plot_canvas.draw_idle()

    _ui(apply)


def updateOutput(long, OutputLabel):
    def _do():
        OutputLabel.moveCursor(QTextCursor.MoveOperation.End)
        OutputLabel.insertPlainText(long)
        OutputLabel.ensureCursorVisible()
    _ui(_do)


def updateParameters(A, C, E, Y, T, prediction, pads, a_label, C_label, eff_mod_label, youngs_mod_label, time_label, pad_label, prediction_label, df, j):
    if A < 0.001:
        formatted_A = '{:0.3e}'.format(A)
    else:
        formatted_A = '{:0.3f}'.format(A)
    if C > 9999:
        formatted_C = '{:0.3e}'.format(C)
    else:
        formatted_C = '{:0.3f}'.format(C)
    formatted_E = '{:0.3f}'.format(E)
    formatted_Y = '{:0.3f}'.format(Y)
    formatted_T = '{:0.0f}'.format(T)
    # pad_text = "Pad 1: " + str(pads[1]) + "\n\nPad 2: " + str(pads[2]) + "\n\nPad 3: " + str(pads[3]) + "\n\nPad 4: " + str(pads[4]) + "\n\nPad 5: " + str(pads[5]) + "\n\nPad 6: " + str(pads[6]) + "\n\nPad 7: " + str(pads[7])
    pad_text = "Pad 0: " + str(pads[1]) + "\n\nPad 1: " + str(pads[2]) + "\n\nPad 2: " + str(pads[3]) + "\n\nPad 3: " + str(pads[4]) + "\n\nPad 4: " + str(pads[5]) + "\n\nPad 5: " + str(pads[6]) + "\n\nPad 6: " + str(pads[7]) + "\n\nPad 7: " + str(pads[8])
    arr = [*pads[1:], formatted_A, formatted_C, formatted_E, formatted_Y, formatted_T, prediction]
    k = j.get()
    df.insert(df.shape[1], 'Sweep ' + str(k), arr)
    a_label.setText("α: " + formatted_A)
    C_label.setText("C: " + formatted_C)
    eff_mod_label.setText("Effective modulus: " + formatted_E)
    youngs_mod_label.setText("Young's modulus: " + formatted_Y)
    time_label.setText("Time (ms): " + formatted_T)
    pad_label.setText(pad_text)
    prediction_label.setText("Predicted trimester: " + prediction)
    prediction_label.setStyleSheet('color: red;' if prediction == 'Abnormal' else '')


def _clearTabs(notebook):
    while notebook.count():
        page = notebook.widget(0)
        notebook.removeTab(0)
        page.deleteLater()
    notebook.hide()


def reset(OutputLabel, notebook, df, j):
    # Row template comes from config so it always matches the width of the rows
    # that updateParameters() will insert. Spelling it out here is what let the
    # 7-pad and 8-pad versions drift apart.
    config.reset_dataframe(df)
    _clearTabs(notebook)
    OutputLabel.clear()
    j.set(1)


def exportCSV(df, OutputLabel, parent=None):
    entered, ok = QInputDialog.getText(parent, "Export CSV", "Enter filename:")
    if not ok:
        return
    name = entered.strip()
    if not name:
        date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
        name = 'sweep_data_' + date
    updateOutput("\nData exported to CSV file: " + name + ".csv", OutputLabel)
    df.to_csv(f'{name}.csv', index=False)


def delete(j, df, notebook, OutputLabel):
    # currentIndex() is -1 when there are no tabs (fresh start, post-reset, or
    # the last sweep already deleted).
    index = notebook.currentIndex()
    if index < 0:
        updateOutput("\nNo sweep to delete\n", OutputLabel)
        return
    df.drop(df.columns[index+1], axis=1, inplace=True)
    page = notebook.widget(index)
    notebook.removeTab(index)
    page.deleteLater()
    long_text = "\nSweep " + str(index + 1) + " deleted"
    updateOutput(long_text, OutputLabel)
    k = j.get()
    if k == 2:
        j.set(1)
        _clearTabs(notebook)
    else:
        for i in range(index, k-2):
            notebook.setTabText(i, 'Sweep ' + str(i+1))
            df.rename(columns={df.columns[i+1]: 'Sweep ' + str(i+1)}, inplace=True)
        j.set(k - 1)

# Endoscope output

def setupCameraView(parent=None):
    view = QLabel(parent)
    view.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # Ignored size policy stops each new frame from growing the label (and the window).
    view.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
    view.setMinimumSize(30, 70)
    timer = QTimer(view)
    camera = {'view': view, 'cap': None, 'timer': timer}
    timer.timeout.connect(lambda: updateFrame(camera))
    return camera


def updateFrame(camera):
    cap = camera['cap']
    ret, frame = cap.read() if cap is not None else (False, None)
    if not ret:
        camera['timer'].stop()
        return
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = frame.shape
    img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
    view = camera['view']
    view.setPixmap(QPixmap.fromImage(img).scaled(
        view.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


def stopCamera(camera):
    camera['timer'].stop()
    if camera['cap'] is not None:
        camera['cap'].release()
        camera['cap'] = None


def changeSweepSettings(presStart, presIncr, presNumIncr, voltThresh, ser, OutputLabel):
    # Errors are logged and returned rather than raised: an exception escaping a
    # Qt button handler can take the whole app down.
    try:
        start = float(presStart.text())
        incr = float(presIncr.text())
        num_incr = int(float(presNumIncr.text()))
        float(voltThresh.text())
    except ValueError:
        updateOutput("\nSweep settings must all be numbers", OutputLabel)
        return
    maxPres = start + incr * num_incr

    if start > 0:
        updateOutput("\nPressure must begin at 0 kPa or less", OutputLabel)
        return
    elif maxPres < -50:
        updateOutput("\nPressure must be under 50 kPa", OutputLabel)
        return

    accepted, rejected = communication.applySweepSettings(
        ser, presStart.text(), presIncr.text(), presNumIncr.text(), voltThresh.text())

    updateOutput("\nSweep Settings Changed:"
                 f"\nStart: {presStart.text()}"
                 f"\nIncrement: {presIncr.text()}"
                 f"\nNumber of Increments: {presNumIncr.text()}\n", OutputLabel)

    if accepted is None:
        updateOutput("Contact Voltage: NO CONFIRMATION from device, threshold may be unchanged\n", OutputLabel)
    elif rejected is not None:
        updateOutput(f"Contact Voltage: REJECTED {rejected} V (must be 0-5 V), still using {accepted} V\n", OutputLabel)
    else:
        updateOutput(f"Contact Voltage: {accepted} V confirmed\n", OutputLabel)


def runCalibratePressure(ser, OutputLabel):
    def on_event(event):
        if event[0] == 'log':
            updateOutput(event[1], OutputLabel)
        elif event[0] == 'aborted':
            updateOutput(f"\nCalibration aborted: {event[1]}\n", OutputLabel)

    voltages, pressures = communication.readCalibration(ser, on_event)
    if voltages is None:
        return

    slope, intercept, r_squared = fit_calibration(pressures, voltages)
    updateOutput(f"Slope: {slope}\n", OutputLabel)
    updateOutput(f"Intercept: {intercept}\n", OutputLabel)
    updateOutput(f"R-Squared: {r_squared}\n", OutputLabel)
    # updateOutput(communication.sendCalibration(ser, slope, intercept), OutputLabel)
    communication.sendCalibration(ser, slope, intercept)


def threadedCalibratePressure(ser, OutputLabel):
    threading.Thread(target=runCalibratePressure, args=(ser, OutputLabel)).start()


def runCalibCheck(ser, OutputLabel):
    def on_event(event):
        if event[0] == 'log':
            updateOutput(event[1], OutputLabel)
        elif event[0] == 'aborted':
            updateOutput(f"\nCalib check: {event[1]}\n", OutputLabel)

    communication.calibCheck(ser, on_event)


def _makeResultLabel(parent):
    label = QLabel(parent)
    label.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    label.setMargin(4)
    return label


def runPressureSweep(ser, strain, j, df, notebook, OutputLabel, camera, btn, live_plot_holder=None, k=1):
    def on_event(event):
        kind = event[0]
        if kind == 'pressure':
            updateLivePressurePlot(live_plot_holder, *event[1:])
        elif kind == 'contact':
            markPressureContact(live_plot_holder, *event[1:])
        elif kind == 'log':
            updateOutput(event[1], OutputLabel)
        elif kind == 'aborted':
            updateOutput(f"\nSweep aborted: {event[1]}\n", OutputLabel)

    pads, elapsed_ms = communication.pressureSweep(ser, on_event)

    if pads is not None:
        x, y = align_data(strain, pads)
        coefficients, eff_mod, youngs_mod, _ = analyze_data(x, y)

        def build(x=x, y=y, coefficients=coefficients, eff_mod=eff_mod,
                  youngs_mod=youngs_mod, elapsed=elapsed_ms, pads=pads.copy()):
            fig = Figure(figsize=(3, 2), layout='constrained')
            ax = fig.add_subplot()
            strain_min, strain_max = 1.0, 2.5
            ax.set_xlim([strain_min, strain_max])
            ax.set_title("Stress Strain Curve")
            ax.set_ylabel("Pressure (kPa)")
            ax.set_xlabel("Strain Ratio")

            graph = QWidget()
            layout = QGridLayout(graph)
            canvas_new = FigureCanvasQTAgg(fig)
            layout.addWidget(canvas_new, 0, 0, 1, 2)
            layout.setRowStretch(0, 1)
            layout.setColumnStretch(0, 1)
            layout.setColumnStretch(1, 1)
            curve_x = np.linspace(strain_min, strain_max, 300)
            ax.plot(curve_x, func(curve_x, *coefficients), 'r-')
            youngs_mod_line = lambda v: youngs_mod * v - youngs_mod
            ax.plot(curve_x, youngs_mod_line(curve_x), 'g--')
            ax.scatter(x, -y, s=4, c='black')
            canvas_new.draw()

            a_label = _makeResultLabel(graph)
            C_label = _makeResultLabel(graph)
            eff_mod_label = _makeResultLabel(graph)
            youngs_mod_label = _makeResultLabel(graph)
            time_label = _makeResultLabel(graph)
            for row, label in enumerate([a_label, C_label, eff_mod_label, youngs_mod_label, time_label], start=1):
                layout.addWidget(label, row, 0)
            pad_label = _makeResultLabel(graph)
            layout.addWidget(pad_label, 1, 1, 5, 1)
            prediction_label = _makeResultLabel(graph)
            layout.addWidget(prediction_label, 6, 0, 1, 2)

            updateParameters(*coefficients, eff_mod, youngs_mod, elapsed, predict_trimester(youngs_mod), pads, a_label, C_label, eff_mod_label, youngs_mod_label, time_label, pad_label, prediction_label, df, j)

            notebook.addTab(graph, 'Sweep ' + str(k))
            notebook.show()
            notebook.setCurrentIndex(k-1)
            j.set(k+1)

        _ui(build)

    _ui(lambda: setButtonAction(btn, "Open Camera", lambda: openCamera(camera, OutputLabel, btn, ser, strain, j, df, notebook, live_plot_holder)))


def threadedPressureSweep(ser, strain, j, df, notebook, OutputLabel, camera, btn, live_plot_holder=None):
    # The camera timer lives on the GUI thread, so stop it here before the sweep
    # thread starts rather than releasing the camera from inside that thread.
    stopCamera(camera)
    setupLivePressurePlot(live_plot_holder)
    k = j.get()
    threading.Thread(target=runPressureSweep,
                     args=(ser, strain, j, df, notebook, OutputLabel, camera, btn, live_plot_holder),
                     kwargs={'k': k}).start()


def openCamera(camera, OutputLabel, btn, ser, strain, j, df, notebook, live_plot_holder=None):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        updateOutput("Error: Could not open camera.", OutputLabel)
    camera['cap'] = cap
    camera['timer'].start(15)
    setButtonAction(btn, "Pressure Sweep", lambda: threadedPressureSweep(ser, strain, j, df, notebook, OutputLabel, camera, btn, live_plot_holder))
