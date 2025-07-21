from tkinter import *
import tkinter as tk 
import serial
from time import sleep
import scipy


commPort = '/dev/cu.usbmodem11201'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Functions
def calibratePressure(voltage, pressure):
    ser.write(b'p')
    for i in range(14):
        arduinoData_string = ser.readline().decode('ascii')
        print(arduinoData_string)
        try:
            arduinoData_float = float(arduinoData_string)   # Convert to float
            voltage.append(arduinoData_float)           # Add first data points to voltage

        except:                                             # Pass if data point is bad                               
            pass
    for i in range(14, 26):
        arduinoData_string = ser.readline().decode('ascii')
        print(arduinoData_string)
        try:
            arduinoData_float = float(arduinoData_string)   # Convert to float
            pressure.append(arduinoData_float)           # Add first data points to voltage

        except:                                             # Pass if data point is bad                               
            pass
    print(voltage)
    print(pressure)
    regressResult = scipy.stats.linregress(pressure, voltage)
    
    slope = regressResult.slope
    intercept = regressResult.intercept
    
    print(slope)
    print(intercept)
    voltage = []
    pressure = []

    sleep(0.5)
    # Send slope and intercept to Arduino
    ser.write(b'r')
    slope = str(slope) + '\r'
    intercept = str(intercept) + '\r'
    ser.write(intercept.encode())   
    sleep(0.1)
    ser.write(slope.encode())
    sleep(0.1)
def pressureSweep():
    ser.write(b's')
def changeSweepSettings():
    ser.write(b'i')
    pres_start = presStart.get() + '\r'
    pres_incr = presIncr.get() + '\r'
    pres_num_incr = presNumIncr.get() + '\r'
    ser.write(pres_start.encode())
    sleep(0.1)
    ser.write(pres_incr.encode())
    sleep(0.1)
    ser.write(pres_num_incr.encode())
    sleep(0.1)
    

# Create empty arrays for later use
voltage = []
pressure = []

# Window
win = Tk() 
win.title('Stress Strain Testing')
win.minsize(200,60)

# Button widget
calibrateBtn = tk.Button(win, text='Calibrate', command=lambda : calibratePressure(voltage, pressure))
calibrateBtn.grid(row=1, column=1)

# Button widget
sweepButton = tk.Button(win, text='Pressure Sweep', command=pressureSweep)
sweepButton.grid(row=1, column=2)

# Button widget
set = tk.Button(win, text="Set Pressure Settings", command=changeSweepSettings)
set.grid(row=1, column=0)

# Entry widgets
presStart = tk.Entry(win, bd=6, width=8)
presStart.grid(column=0, row=0)
presIncr = tk.Entry(win, bd=6, width=8)
presIncr.grid(column=1, row=0)
presNumIncr = tk.Entry(win, bd=6, width=8)
presNumIncr.grid(column=2, row=0)

win.mainloop()