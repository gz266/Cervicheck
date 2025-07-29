from tkinter import *
import tkinter as tk 
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading

import serial
from time import sleep
import scipy
import numpy as np
from scipy.optimize import curve_fit

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation
matplotlib.use('agg')


commPort = '/dev/cu.usbmodem21301'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Exception
class Pressure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"

# # # # # # 
# Functions
# # # # # #

# Testing functions
def calibratePressure(voltage, p):
    ser.write(b'p')
    v_b = False
    p_b = False
    i = 0
    while True:
        data = ser.readline().decode('ascii')
        updateOutput(data)
        if data.startswith("Done"):
            break
        if data.startswith("Voltage"):
            v_b = True
            p_b = False
            i = 0
        if data.startswith("Pressure"): 
            v_b = False
            p_b = True
            i = 0
        if v_b:
            if i == 0:
                i += 1
            else:
                i += 1
                dataFloat = float(data)   # Convert to float
                voltage.append(dataFloat)   # Add to voltage array
        if p_b:
            if i == 0:
                i += 1
            else: 
                i += 1
                dataFloat = float(data)   # Convert to float
                p.append(dataFloat)         # Add to pressure array
    regressResult = scipy.stats.linregress(p, voltage)
    slope = regressResult.slope
    intercept = regressResult.intercept
    r_squared = regressResult.rvalue ** 2
    voltage = []
    p = []

    # Send slope and intercept to Arduino
    ser.write(b'r')
    slope = str(slope) + '\r'
    intercept = str(intercept) + '\r'
    r_squared = str(r_squared) + '\r'
    updateOutput('Slope: '+ slope)
    updateOutput('Intercept: '+ intercept)
    updateOutput('R-Squared: ' + r_squared)
    ser.write(slope.encode())   
    sleep(0.1)
    ser.write(intercept.encode())
    sleep(0.1)
    sweepButton.config(state='normal')

def pressureSweep():
    global j
    ser.write(b's') 
    b = False
    pressure = np.zeros(8)
    if j > 1:
        while True:
            data = ser.readline().decode('ascii')
            # print(data)
            updateOutput(data)
            if data.startswith("Done"):
                b = True
                i = 0
            if data.startswith("Time"):
                time = float(data[6:])
                # updateTime(time)
                try:
                    x, y = align_data(strain, pressure)
                    coefficients, modulus = analyze_data(x, y)
                    fig_new, ax_new = plt.subplots(figsize=(3, 2), layout='constrained')
                    ax_new.set_ylim([0, 50])                              # Set Y axis limit of plot
                    ax_new.set_xlim([1, 2.5])  
                    ax_new.set_title("Stress Strain Curve")                        # Set title of figure
                    ax_new.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
                    ax_new.set_xlabel("Percent Strain (%)")         # Set title of x axis

                    graph_new = tk.Frame()
                    notebook.add(graph_new, text = 'Sweep ' + str(j))

                    canvas_new = FigureCanvasTkAgg(fig_new, master=graph_new)
                    canvas_widget_new = canvas_new.get_tk_widget()
                    canvas_widget_new.grid(row=0, column=0, sticky="NSEW")
                    canvas_widget_new.grid_rowconfigure(0, weight=1)
                    canvas_widget_new.grid_columnconfigure(0, weight=1)
                    ax_new.plot(x, func(x, *coefficients), 'r-')
                    ax_new.scatter(x, -y, s=4, c='black')
                    canvas_new.draw()

                    a_label_new = tk.Text(graph_new, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                    a_label_new.insert(tk.END, "a: ")
                    a_label_new.grid(column=0, row=5, sticky="nsew")
                    C_label_new = tk.Text(graph_new, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                    C_label_new.insert(tk.END, "C: ")
                    C_label_new.grid(column=0, row=6, sticky="nsew")
                    youngs_label_new = tk.Text(graph_new, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                    youngs_label_new.insert(tk.END, "Young's modulus: ")
                    youngs_label_new.grid(column=0, row=7, sticky="nsew")
                    time_label_new = tk.Text(graph_new, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                    time_label_new.insert(tk.END, "Time (ms): ")
                    time_label_new.grid(column=0, row=8, sticky="nsew")

                    updateParameters(*coefficients, modulus, time, a_label_new, C_label_new, youngs_label_new, time_label_new)

                    notebook.select(j-1)
                    j += 1
                except:
                    updateOutput("No pads were contacted")
                break
            if b:
                if i == 0:
                    i = i + 1
                else:
                    data_float = float(data)
                    pressure[i] = data_float
                    i = i + 1

    # Todo: Arduino returns stress strain data, python analyzes and plots it
    else:
        while True:
            data = ser.readline().decode('ascii')
            # print(data)
            updateOutput(data)
            if data.startswith("Done"):
                b = True
                i = 0
            if data.startswith("Time"):
                time = float(data[6:])
                # updateTime(time)
                try:
                    x, y = align_data(strain, pressure)
                    coefficients, modulus = analyze_data(x, y)
                    xlin = np.linspace(1,x[len(x)-1], 1000)
                    ax.plot(xlin, func(xlin, *coefficients), 'r-')
                    ax.scatter(x, -y, s=4, c='black')
                    updateParameters(*coefficients, modulus, time, a_label, C_label, youngs_label, time_label)
                    canvas.draw()
                    j += 1
                except:
                    updateOutput("No pads were contacted")
                break
            if b:
                if i == 0:
                    i = i + 1
                else:
                    data_float = float(data)
                    pressure[i] = data_float
                    i = i + 1


    # Update Sweep Details Text Widget

    # User needs to be aware of what is going on during the sweep
    # Include Impedance Outputs
    # Time Elapsed

def func(x, a, C):
    return a* C * ((x ** 2) - (1 / x))* np.exp(a * ((x ** 2) + (2 / x) - 3))

def align_data(stretch, stress):
    """
    Aligns the data based on the stretch and strain values.
    
    Parameters:
    stretch (1D array): Stretch factor for the analysis.
    stress (1D array): Strain data for the trial.
    
    Returns:
    aligned_stretch (1D array): Aligned stretch values.
    aligned_strain (1D array): Aligned stress values.
    """

    aligned_stretch = stretch
    aligned_stress = stress

    for i in range(1, len(stress)):
        if stress[i] == 0.:
            aligned_stress = aligned_stress[:i]
            aligned_stretch = aligned_stretch[:i]
            return aligned_stretch, aligned_stress
    
    return aligned_stretch, aligned_stress

def analyze_data(stretch, stress):
    """
    Analyze ONE set of data based on the specified fit type and stretch.
    
    Parameters:
    stretch (1D array): Stretch factor for the analysis.
    varargin (1D array): Stress data for the trial.
    
    Returns:
    popt (array): Optimal values for the parameters of the fit.
    eff_modulus (float): Effective modulus calculated from the fit parameters.
    """

    # TODO 

    eff_modulus = 0
    x = stretch
    y = stress* -1

    popt, pcov = curve_fit(func, x, y, maxfev=100000)
    #fit_values = fit(stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
    #coeff = coeffvalues(fit_values)
    
    alpha_coeff = 0
    C_coeff = 0
    eff_modulus = popt[0]*popt[1]*(-0.052*(popt[0]**3)+0.252*(popt[0]**2)+(0.053*popt[0])+1.09)
    
    return popt, eff_modulus

def changeSweepSettings():
    maxPres = int(presStart.get()) + int(presIncr.get()) * int(presNumIncr.get())
    if int(presStart.get()) > 0:
        long_text = "\nPressure must begin at 0 kPa or less"
        updateOutput(long_text)
        raise Pressure("Pressure must begin at 0 kPa or less")
    elif maxPres < -50:
        long_text = "\nPressure must be under 50 kPa"
        updateOutput(long_text)
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
    long_text = "\nSweep Settings Changed:\nStart: " + pres_start + "Increment: " + pres_incr + "Number of Increments: " + pres_num_incr
    updateOutput(long_text)

# Visuals functions
def updateOutput(long):
    OutputLabel.insert(tk.END, long)
    OutputLabel.see('end')
def updateParameters(A, C, Y, T, a_label, C_label, youngs_label, time_label):
    if A < 0.001:
        formatted_A = '{:0.3e}'.format(A)
    else:
        formatted_A = '{:0.3f}'.format(A)
    if C > 1000:
        formatted_C = '{:0.3e}'.format(C)
    else:
        formatted_C = '{:0.3f}'.format(C)
    formatted_Y = '{:0.3f}'.format(Y)
    formatted_T = '{:0.0f}'.format(T)
    # text = "a: " + str(formatted_A) + '\nC: ' + str(formatted_C) + "\nYoung's modulus: " + str(formatted_Y) + '\nTime (ms): ' + str(formatted_T)
    # ax.text(2, 1.5, text)
    a_label.delete(1.0, tk.END)
    a_label.insert(tk.END, "a: ")
    a_label.insert(tk.END, formatted_A)
    a_label.config(state='disabled')
    C_label.delete(1.0, tk.END)
    C_label.insert(tk.END, "C: ")
    C_label.insert(tk.END, formatted_C)
    C_label.config(state='disabled')
    youngs_label.delete(1.0, tk.END)
    youngs_label.insert(tk.END, "Young's modulus: ")
    youngs_label.insert(tk.END, formatted_Y)
    youngs_label.config(state='disabled')
    time_label.delete(1.0, tk.END)
    time_label.insert(tk.END, "Time (ms): ")
    time_label.insert(tk.END, formatted_T)
    time_label.config(state='disabled')
# def updateTime(T):
#     time_label.delete(1.0, tk.END)
#     time_label.insert(tk.END, "Time (ms): ")
#     time_label.insert(tk.END, T)

# Thread functions so textbox will update in real time

def threadedPressureSweep():
    threading.Thread(target=pressureSweep).start()
def threadedCalibratePressure(voltage, pressure):
    threading.Thread(target=lambda : calibratePressure(voltage, pressure)).start()
    

# Create dummy variables for later use
voltageLinReg = []
pressureLinReg = []

long_text = ""
a = 0
C = 0
Y = 0
strain = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])
j = 1

## Gui Interface
# Window
win = Tk() 
win.grid_rowconfigure(0, weight=1)
# win.grid_rowconfigure(1, weight=1)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(2, weight=1)
win.grid_columnconfigure(4, weight=1)
frame1 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
# frame2 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame3 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
# frame4 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)

frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
# frame2.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
frame3.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")
# frame4.grid(row=1, column=4, padx=10, pady=10, sticky="nsew")

win.title('Stress Strain Testing')
win.minsize(200,60)

## Frame 1 Widgets
# Calibrate widget
calibrateBtn = tk.Button(frame1, text='Calibrate Pressure', command=lambda : threadedCalibratePressure(voltageLinReg, pressureLinReg))
calibrateBtn.grid(row=4, column=1)
# calibrateBtn.config(width=8, height=1)

# Pressure Sweep Widget
sweepButton = tk.Button(frame1, text='Pressure Sweep', command=threadedPressureSweep)
sweepButton.grid(row=5, column=1)
# sweepButton.config(state='disabled')
# sweepButton.config(width=8, height=1)

# Set Pressure Widget
set = tk.Button(frame1, text="Set Pressure Settings", command=changeSweepSettings)
set.grid(row=3, column=1)
# set.config(width=8, height=1)

# Entry widgets
def callback(P):
    return str.isdigit(P) or P=='' or (str(P)[0] == '-' and str.isdigit(P[1:])) or str(P) == '-'
vcmd = (win.register(callback))

presStart = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
presIncr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
presNumIncr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))

presStart.insert(0, "-1")
presIncr.insert(0, "-1")
presNumIncr.insert(0, "20")
presStart.grid(column=1, row=0, sticky="nsew")
presIncr.grid(column=1, row=1, sticky="nsew")
presNumIncr.grid(column=1, row=2, sticky="nsew")

presStartLabel = tk.Label(frame1, text='Starting Pressure (kPa)')
presIncrLabel = tk.Label(frame1, text='Pressure Increment (kPa)')
presNumIncrLabel = tk.Label(frame1, text='Number of Increments')
presStartLabel.grid(column=0, row=0, sticky="nsew")
presIncrLabel.grid(column=0, row=1, sticky="nsew")
presNumIncrLabel.grid(column=0, row=2, sticky="nsew")

# frame1.grid_rowconfigure(0, weight=1)
# frame1.grid_rowconfigure(1, weight=1)
# frame1.grid_rowconfigure(2, weight=1)
# frame1.grid_rowconfigure(3, weight=1)
# frame1.grid_rowconfigure(4, weight=1)
# frame1.grid_rowconfigure(5, weight=1)

# frame1.grid_columnconfigure(0, weight=1)
# frame1.grid_columnconfigure(1, weight=1)

## Frame 2 Widgets
# Matplotlib Figure
fig, ax = plt.subplots(figsize=(3, 2), layout='constrained')  # Smaller figure, layout adjusted to prevent overlap

ax.set_ylim([0, 50])                              # Set Y axis limit of plot
ax.set_xlim([1, 2.5])  
ax.set_title("Stress Strain Curve")                        # Set title of figure
ax.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
ax.set_xlabel("Percent Strain (%)")         # Set title of x axis

# Frame to hold the canvas
notebook = ttk.Notebook(win)
notebook.grid(column=2, row=0, sticky='NSEW')
graph = tk.Frame()
notebook.add(graph, text = 'Sweep 1')
# frame2.grid(column=1, row=0, sticky="NSEW") 
# frame2.grid_rowconfigure(0, weight=1)
# frame2.grid_columnconfigure(0, weight=1)
canvas = FigureCanvasTkAgg(fig, master=graph)
canvas_widget = canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, sticky="NSEW")
canvas_widget.grid_rowconfigure(0, weight=1)
canvas_widget.grid_columnconfigure(0, weight=1)

## Frame 3

# Dynamic Text Outputs
o = tk.Label(frame3, text='Test Outputs')
o.grid(column=0, row=0, sticky="nsew")

OutputLabel = ScrolledText(frame3, width=30, height=30, wrap=tk.WORD, relief=tk.RAISED, borderwidth=1)
OutputLabel.grid(column=0, row=1, sticky="nsew")

OutputLabel.insert(tk.END, long_text)
# OutputLabel.configure(state = 'disabled')

# Text Widget
a_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
a_label.insert(tk.END, "a: ")
a_label.grid(column=0, row=5, sticky="nsew")
C_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
C_label.insert(tk.END, "C: ")
C_label.grid(column=0, row=6, sticky="nsew")
youngs_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
youngs_label.insert(tk.END, "Young's modulus: ")
youngs_label.grid(column=0, row=7, sticky="nsew")
time_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
time_label.insert(tk.END, "Time (ms): ")
time_label.grid(column=0, row=8, sticky="nsew")

win.mainloop()