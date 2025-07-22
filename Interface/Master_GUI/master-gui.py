from tkinter import *
import tkinter as tk 
import serial
from time import sleep
import scipy

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation


commPort = '/dev/cu.usbmodem2101'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Exception
class Pressure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"
    
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
    # Todo: Arduino returns stress strain data, python analyzes and plots it

    # Arduino Returns
    # Pad Number
    # Current Pressure
    # Sweep x of y

    # Else Return
    # Setting pressure to x kPa

    # Update Sweep Details Text Widget

    # User needs to be aware of what is going on during the sweep
    # Include Impedance Outputs
    # Time Elapsed

    # Data Analysis
    # Plotting

def changeSweepSettings():
    maxPres = int(presStart.get()) + int(presIncr.get()) * int(presNumIncr.get())
    if int(presStart.get()) > 0:
        raise Pressure("Pressure must begin at 0 kPa or less")
    elif maxPres < -50:
        raise Pressure("Pressure must be under 50 kPa")
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

## Gui Interface
# Window
win = Tk() 
frame1 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame2 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)

frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame2.grid(row=0, column=5, padx=10, pady=10, sticky="nsew")

win.title('Stress Strain Testing')
win.minsize(200,60)

## Frame 1 Widgets
# Calibrate widget
calibrateBtn = tk.Button(frame1, text='Calibrate', command=lambda : calibratePressure(voltage, pressure))
calibrateBtn.grid(row=4, column=1)

# Pressure Sweep Widget
sweepButton = tk.Button(frame1, text='Pressure Sweep', command=pressureSweep)
sweepButton.grid(row=5, column=1)

# Set Pressure Widget
set = tk.Button(frame1, text="Set Pressure Settings", command=changeSweepSettings)
set.grid(row=3, column=1)

# Entry widgets
presStart = tk.Entry(frame1, bd=6, width=8)
presIncr = tk.Entry(frame1, bd=6, width=8)
presNumIncr = tk.Entry(frame1, bd=6, width=8)

presStart.insert(0, "-1")
presIncr.insert(0, "-1")
presNumIncr.insert(0, "20")
presStart.grid(column=1, row=0)
presIncr.grid(column=1, row=1)
presNumIncr.grid(column=1, row=2)

presStartLabel = tk.Label(frame1, text='Starting Pressure (kPa)')
presIncrLabel = tk.Label(frame1, text='Pressure Increment (kPa)')
presNumIncrLabel = tk.Label(frame1, text='Number of Increments')
presStartLabel.grid(column=0, row=0)
presIncrLabel.grid(column=0, row=1)
presNumIncrLabel.grid(column=0, row=2)

## Frame 2 Widgets
# Matplotlib Figure
fig, ax = plt.subplots(figsize=(3, 2))  # Smaller figure

# Frame to hold the canvas
frame = tk.Frame(frame2, width=150, height=150)
frame.grid(column=5, row=1, rowspan=2, sticky="NSEW")  
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, sticky="NSEW")

graphLabel = tk.Label(frame2, text='Stress Strain Graph')
graphLabel.grid(column=5, row=0)

# Dynamic Text Outputs
presNumIncrLabel = tk.Label(frame1, text='Number of Increments')
presStartLabel.grid(column=0, row=0, rowspan=3, columnspan=3)
presIncrLabel.grid(column=0, row=1)
presNumIncrLabel.grid(column=0, row=2)

# Text Widget


win.mainloop()