import sys
import traceback
from time import sleep
import serial
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QLineEdit,
                             QPushButton, QPlainTextEdit, QTabWidget, QGridLayout,
                             QHBoxLayout, QVBoxLayout)
import config
from gui import (reset, exportCSV, delete, openCamera, threadedCalibratePressure, runCalibCheck,
                 changeSweepSettings, setupPadIndicator, setupCameraView, stopCamera,
                 makeNumberValidator, SweepCounter)


def _printException(exc_type, exc_value, exc_tb):
    # PyQt6 aborts the whole app on an exception escaping a button handler unless
    # sys.excepthook is replaced. Print it and keep running, as Tkinter did.
    traceback.print_exception(exc_type, exc_value, exc_tb)


def _panel():
    frame = QFrame()
    frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
    return frame


def _title(text):
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def main():
    sys.excepthook = _printException

    if '--demo' in sys.argv:
        # No device: replay recorded hardware transcripts instead.
        from demo_serial import DemoSerial
        ser = DemoSerial()
    else:
        commPort = 'COM6'
        ser = serial.Serial(commPort, baudrate = 115200, timeout = 5)
        sleep(2)


    # Stretch ratios and the dataframe row template are both derived from
    # config.PAD_COUNT so they cannot drift apart. To change the pad count, edit
    # config.py only.
    strain = config.STRAIN_RATIOS

    # Pandas dataframe to hold all data
    df = config.new_dataframe()

    ## Gui Interface
    # Window
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle('Stress Strain Testing')
    win.setMinimumSize(200, 60)

    central = QWidget()
    win.setCentralWidget(central)
    columns = QHBoxLayout(central)

    frame1 = _panel()
    frame3 = _panel()
    frame2 = _panel()

    j = SweepCounter(1)

    ## Frame 3: live pressure plot and pad contact picture
    frame3_layout = QVBoxLayout(frame3)
    frame3_layout.addWidget(_title('Live Pressure'))
    livePlotArea = _panel()
    QVBoxLayout(livePlotArea)
    frame3_layout.addWidget(livePlotArea, stretch=1)
    livePlotStatus = _title('Waiting for sweep')
    frame3_layout.addWidget(livePlotStatus)
    frame3_layout.addWidget(_title('Pad Contact'))
    pad_indicator = setupPadIndicator()
    frame3_layout.addWidget(pad_indicator)
    live_plot_holder = {'parent': livePlotArea, 'status': livePlotStatus, 'pad_indicator': pad_indicator}

    ## Frame 1 Widgets
    frame1_layout = QGridLayout(frame1)
    frame1_layout.setColumnStretch(0, 1)
    frame1_layout.setColumnStretch(1, 1)
    frame1_layout.setRowStretch(7, 1)

    # Entry widgets
    validator = makeNumberValidator(frame1)

    presStart = QLineEdit("-1")
    presIncr = QLineEdit("-1")
    presNumIncr = QLineEdit("20")
    voltThresh = QLineEdit("4.5")
    for row, (text, entry) in enumerate([('Starting Pressure (kPa)', presStart),
                                         ('Pressure Increment (kPa)', presIncr),
                                         ('Number of Increments', presNumIncr),
                                         ('Contact Voltage (V)', voltThresh)]):
        entry.setValidator(validator)
        frame1_layout.addWidget(_title(text), row, 0)
        frame1_layout.addWidget(entry, row, 1)

    # Notebook for graphs (hidden until the first sweep finishes)
    notebook = QTabWidget()
    notebook.setUsesScrollButtons(True)
    notebook.hide()

    ## Frame 2 Widgets

    # Dynamic Text Outputs
    frame2_layout = QVBoxLayout(frame2)
    frame2_layout.addWidget(_title('Test Outputs'))
    OutputLabel = QPlainTextEdit()
    OutputLabel.setReadOnly(True)
    frame2_layout.addWidget(OutputLabel, stretch=1)

    # Endoscope view
    camera = setupCameraView()
    frame1_layout.addWidget(camera['view'], 7, 0, 1, 2)

    # Buttons
    # Set Pressure Widget
    setBtn = QPushButton("Set Sweep Settings")
    setBtn.clicked.connect(lambda: changeSweepSettings(presStart, presIncr, presNumIncr, voltThresh, ser, OutputLabel))
    frame1_layout.addWidget(setBtn, 4, 1)

    # Calibrate widget
    calibrateBtn = QPushButton('Calibrate Pressure')
    calibrateBtn.clicked.connect(lambda: threadedCalibratePressure(ser, OutputLabel))
    frame1_layout.addWidget(calibrateBtn, 5, 1)

    # Pressure Sweep Widget (switches to "Pressure Sweep" once the camera is open)
    sweepButton = QPushButton('Open Camera')
    sweepButton.clicked.connect(lambda: openCamera(camera, OutputLabel, sweepButton, ser, strain, j, df, notebook, live_plot_holder))
    frame1_layout.addWidget(sweepButton, 6, 1)

    # --- TROUBLESHOOTING: manual calibration check button ---
    calibCheckBtn = QPushButton('Calib Check')
    calibCheckBtn.clicked.connect(lambda: runCalibCheck(ser, OutputLabel))
    frame1_layout.addWidget(calibCheckBtn, 8, 1)
    # --- END TROUBLESHOOTING ---

    # Export CSV Widget
    exportBtn = QPushButton('Export CSV')
    exportBtn.clicked.connect(lambda: exportCSV(df, OutputLabel, win))
    frame1_layout.addWidget(exportBtn, 4, 0)

    # Reset Widget
    resetBtn = QPushButton('Reset')
    resetBtn.clicked.connect(lambda: reset(OutputLabel, notebook, df, j))
    frame1_layout.addWidget(resetBtn, 5, 0)

    # Delete Widget
    deleteBtn = QPushButton('Delete Sweep')
    deleteBtn.clicked.connect(lambda: delete(j, df, notebook, OutputLabel))
    frame1_layout.addWidget(deleteBtn, 6, 0)

    # Column order matches the old grid: controls | live pressure | sweeps | outputs
    columns.addWidget(frame1, stretch=1)
    columns.addWidget(frame3, stretch=1)
    columns.addWidget(notebook, stretch=1)
    columns.addWidget(frame2, stretch=1)

    def cleanup():
        stopCamera(camera)
        ser.close()
    app.aboutToQuit.connect(cleanup)

    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
