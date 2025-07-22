from tkinter import *
import tkinter as tk 
from tkinter.scrolledtext import ScrolledText
import threading

import serial
from time import sleep
import scipy

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation


commPort = '/dev/cu.usbmodem11201'
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
    b = False
    # Todo: Arduino returns stress strain data, python analyzes and plots it
    while True:
        data = ser.readline().decode('ascii')
        updateOutput(data, 100, 100, 100)
        if data.startswith("Done"):
            b = True
        if b:
            try:
                data_float = float(data)
            except:
                pass
            try:
                pressure.append(data_float)
            except:
                pass
        if data.startswith("Time"):
            break

    
    # Arduino Returns
        # Sweep x of y
        # Pad Number
        # Current Pressure

    # Else Return
        # Setting Pressure to x kPa!
        # Performming Impedance Sweep!
        # No Contact Made!
        # Contact Made!


    # Update Sweep Details Text Widget

    # User needs to be aware of what is going on during the sweep
    # Include Impedance Outputs
    # Time Elapsed
def threadedPressureSweep():
    threading.Thread(target=pressureSweep).start()
def updateOutput(long, A, C, Y):
    OutputLabel.insert(tk.END, long)

def analysis():
    pass
    # a_label.insert(tk.END, "134")
    # C_label.insert(tk.END, "0.5")
    # youngs_label.insert(tk.END, "2000")

def changeSweepSettings():
    maxPres = int(presStart.get()) + int(presIncr.get()) * int(presNumIncr.get())
    if int(presStart.get()) > 0:
        long_text = "Pressure must begin at 0 kPa or less"
        raise Pressure("Pressure must begin at 0 kPa or less")
    elif maxPres < -50:
        long_text = "Pressure must be under 50 kPa"
        raise Pressure("Pressure must be under 50 kPa")
    ser.write(b'i')
    global pres_start, pres_incr, pres_num_incr
    pres_start = presStart.get() + '\r'
    pres_incr = presIncr.get() + '\r'
    pres_num_incr = presNumIncr.get() + '\r'
    ser.write(pres_start.encode())
    sleep(0.1)
    ser.write(pres_incr.encode())
    sleep(0.1)
    ser.write(pres_num_incr.encode())
    sleep(0.1)


    

# Create dummy variables for later use
voltageLinReg = []
pressureLinReg = []
pressure = []
long_text = "Text\n"

## Gui Interface
# Window
win = Tk() 
frame1 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame2 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame3 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame4 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)

frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame2.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
frame3.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")
frame4.grid(row=1, column=4, padx=10, pady=10, sticky="nsew")

win.title('Stress Strain Testing')
win.minsize(200,60)

## Frame 1 Widgets
# Calibrate widget
calibrateBtn = tk.Button(frame1, text='Calibrate', command=lambda : calibratePressure(voltageLinReg, pressureLinReg))
calibrateBtn.grid(row=4, column=1)

# Pressure Sweep Widget
sweepButton = tk.Button(frame1, text='Pressure Sweep', command=threadedPressureSweep)
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

## Frame 3 and 4

# Dynamic Text Outputs
o = tk.Label(frame3, text='Test Outputs')
o.grid(column=0, row=0)

OutputLabel = ScrolledText(frame3, width=30, height=10, wrap=tk.WORD)
OutputLabel.grid(column=0, row=1)

OutputLabel.insert(tk.END, long_text)
# OutputLabel.configure(state = 'disabled')

# Text Widget
a_label = tk.Label(frame3, text='A: ')
a_label.grid(column=0, row=2)
C_label = tk.Label(frame3, text='C: ')
C_label.grid(column=0, row=3)
youngs_label = tk.Label(frame3, text="Young's: ")
youngs_label.grid(column=0, row=4)

## Frame 2 Widgets
# Matplotlib Figure
fig, ax = plt.subplots(figsize=(3, 2))  # Smaller figure
fig.tight_layout()  # Adjust layout to prevent overlap  

ax.set_ylim([0, 50])                              # Set Y axis limit of plot
ax.set_xlim([0, 2])  
ax.set_title("Stress Strain Curve")                        # Set title of figure
ax.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
ax.set_xlabel("Percent Strain (%)")         # Set title of x axis

# Frame to hold the canvas
frame = tk.Frame(frame2)
frame.grid(column=0, row=0, sticky="NSEW") 
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, sticky="NSEW")

win.mainloop()