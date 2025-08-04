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
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation
matplotlib.use('agg')
import cv2
from PIL import Image
from PIL import ImageTk



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

# # # # # # 
# Functions
# # # # # #

# Testing functions
def calibratePressure():
    ser.write(b'p')
    voltage = []
    pressure = []
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
                pressure.append(dataFloat)         # Add to pressure array
    regressResult = scipy.stats.linregress(pressure, voltage)
    slope = regressResult.slope
    intercept = regressResult.intercept
    r_squared = regressResult.rvalue ** 2

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
    global df
    global notebook
    ser.write(b's') 
    b = False
    pressure = np.zeros(8)
    while True:
        data = ser.readline().decode('ascii')
        updateOutput(data)
        if data.startswith("Done"):
            b = True
            i = 0
        if data.startswith("Time"):
            time = float(data[6:])
            try:
                x, y = align_data(strain, pressure)
                coefficients, modulus = analyze_data(x, y)
                fig, ax = plt.subplots(figsize=(3, 2), layout='constrained')
                ax.set_ylim([0, 50])                              # Set Y axis limit of plot
                ax.set_xlim([1, 2.5])  
                ax.set_title("Stress Strain Curve")                        # Set title of figure
                ax.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
                ax.set_xlabel("Percent Strain (%)")         # Set title of x axis

                if j == 1:
                    notebook.grid(column=2, row=0, sticky='NSEW')
                    win.grid_columnconfigure(2, weight=1)
                    notebook.grid_rowconfigure(0, weight=1)
                    notebook.grid_columnconfigure(0, weight=1)
                graph = tk.Frame()
                notebook.add(graph, text = 'Sweep ' + str(j))
                graph.grid_rowconfigure(0, weight=1)
                graph.grid_columnconfigure(0, weight=1)
                graph.grid_columnconfigure(1, weight=1)
                canvas_new = FigureCanvasTkAgg(fig, master=graph)
                canvas_widget_new = canvas_new.get_tk_widget()
                canvas_widget_new.grid(row=0, column=0, columnspan=2, sticky="NSEW")
                canvas_widget_new.grid_rowconfigure(0, weight=1)
                canvas_widget_new.grid_columnconfigure(0, weight=1)
                ax.plot(x, func(x, *coefficients), 'r-')
                ax.scatter(x, -y, s=4, c='black')
                canvas_new.draw()

                a_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                a_label.grid(column=0, row=5, sticky="nsew")
                a_label.config(state='disabled')
                C_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                C_label.grid(column=0, row=6, sticky="nsew")
                C_label.config(state='disabled')
                youngs_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                youngs_label.grid(column=0, row=7, sticky="nsew")
                youngs_label.config(state='disabled')
                time_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
                time_label.grid(column=0, row=8, sticky="nsew")
                time_label.config(state='disabled')
                pad_label = tk.Text(graph, height=12, width=30, relief=tk.RAISED, borderwidth=1)
                pad_label.grid(column=1, row=5, rowspan=4, sticky="nsew")
                pad_label.config(state='disabled')

                updateParameters(*coefficients, modulus, time, pressure, a_label, C_label, youngs_label, time_label, pad_label)

                notebook.select(j-1)
                j += 1
            except:
                updateOutput("No pads were contacted\n")
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

def exportCSV():
    name = None
    name_var = tk.StringVar()
    global df
    def saveName(event=None):
        date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
        name = field.get()
        if name == None:
            name = 'sweep_data_' + date
        name_var.set(name)
        winput.destroy()


    winput = tk.Toplevel()
    winput.wm_geometry("300x150")
    winput.title("Export CSV")

    field = tk.Entry(winput, bd=6, width=30)
    field.grid(row=1, column=0, padx=10, pady=10)
    field.bind("<Return>", saveName)

    button = tk.Button(winput, text="Save", command=saveName)
    button.grid(row=2, column=0, padx=10, pady=10)
    button.configure(width=12, height=1)

    label = tk.Label(winput, text="Enter filename:")
    label.grid(row=0, column=0, padx=10, pady=10)

    winput.mainloop()

    name = name_var.get()
    df.to_csv(f'{name}.csv', index=False)
    long_text = "\nData exported to CSV file:" + name + ".csv"
    updateOutput(long_text)

def reset():
    global j
    global df
    global notebook
    j = 1
    df = pd.DataFrame({'Pad number' : [1, 2, 3, 4, 5, 6, 7, 'α', 'C', 'Young\'s Modulus', 'Time (ms)']})
    notebook.destroy()
    notebook = ttk.Notebook(win)
    win.grid_columnconfigure(2, weight=0)
    OutputLabel.configure(state='normal')
    OutputLabel.delete(1.0, tk.END)
    OutputLabel.configure(state='disabled')
def delete():
    global j
    global df
    global notebook
    index = notebook.index("current")
    df.drop(df.columns[index+1], axis=1, inplace=True)
    notebook.forget(index)
    long_text = "\nSweep " + str(index + 1) + " deleted"
    updateOutput(long_text)
    if j == 2:
        j -= 1
        notebook.destroy()
        notebook = ttk.Notebook(win)
    else:
        for i in range(index, j-2):
            notebook.tab(i, text='Sweep ' + str(i+1))
            df.rename(columns={df.columns[i+1]: 'Sweep ' + str(i+1)}, inplace=True)
        j -= 1

# Visuals functions
def updateOutput(long):
    OutputLabel.configure(state='normal')
    OutputLabel.insert(tk.END, long)
    OutputLabel.see('end')
    OutputLabel.configure(state='disabled')
def updateParameters(A, C, Y, T, pads, a_label, C_label, youngs_label, time_label, pad_label):
    if A < 0.001:
        formatted_A = '{:0.3e}'.format(A)
    else:
        formatted_A = '{:0.3f}'.format(A)
    if C > 9999:
        formatted_C = '{:0.3e}'.format(C)
    else:
        formatted_C = '{:0.3f}'.format(C)
    formatted_Y = '{:0.3f}'.format(Y)
    formatted_T = '{:0.0f}'.format(T)
    for pad in pads:
        formatted_pad = '{:0.2f}'.format(pad)
    pad_text = "Pad 1: " + str(pads[1]) + "\n\nPad 2: " + str(pads[2]) + "\n\nPad 3: " + str(pads[3]) + "\n\nPad 4: " + str(pads[4]) + "\n\nPad 5: " + str(pads[5]) + "\n\nPad 6: " + str(pads[6]) + "\n\nPad 7: " + str(pads[7])
    arr = [*pads[1:], formatted_A, formatted_C, formatted_Y, formatted_T]
    df.insert(df.shape[1], 'Sweep ' + str(j), arr)
    a_label.config(state='normal')
    a_label.delete(1.0, tk.END)
    a_label.insert(tk.END, "α: ")
    a_label.insert(tk.END, formatted_A)
    a_label.config(state='disabled')
    C_label.config(state='normal')
    C_label.delete(1.0, tk.END)
    C_label.insert(tk.END, "C: ")
    C_label.insert(tk.END, formatted_C)
    C_label.config(state='disabled')
    youngs_label.config(state='normal')
    youngs_label.delete(1.0, tk.END)
    youngs_label.insert(tk.END, "Young's modulus: ")
    youngs_label.insert(tk.END, formatted_Y)
    youngs_label.config(state='disabled')
    time_label.config(state='normal')
    time_label.delete(1.0, tk.END)
    time_label.insert(tk.END, "Time (ms): ")
    time_label.insert(tk.END, formatted_T)
    time_label.config(state='disabled')
    pad_label.config(state='normal')
    pad_label.delete(1.0, tk.END)
    pad_label.insert(tk.END, pad_text)
    pad_label.config(state='disabled')

# Thread functions so textbox will update in real time

def threadedPressureSweep():
    threading.Thread(target=pressureSweep).start()
def threadedCalibratePressure():
    threading.Thread(target=calibratePressure).start()

long_text = ""
a = 0
C = 0
Y = 0
strain = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])
j = 1

# Pandas dataframe to hold all data
data = {'Pad number' : [1, 2, 3, 4, 5, 6, 7, 'α', 'C', 'Young\'s Modulus', 'Time (ms)']}
df = pd.DataFrame(data)

## Gui Interface
# Window
win = Tk() 
win.grid_rowconfigure(0, weight=1)
win.grid_columnconfigure(0, weight=1)
win.grid_columnconfigure(4, weight=1)
frame1 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame2 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)

frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

frame1.grid_columnconfigure(0, weight=1)
frame1.grid_columnconfigure(1, weight=1)
frame1.grid_rowconfigure(6, weight=1)

frame2.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")
frame2.grid_rowconfigure(0, weight=1)
frame2.grid_columnconfigure(0, weight=1)
frame2.grid_rowconfigure(1, weight=1)

win.title('Stress Strain Testing')
win.minsize(200,60)

## Frame 1 Widgets
# Calibrate widget
calibrateBtn = tk.Button(frame1, text='Calibrate Pressure', command=threadedCalibratePressure, anchor='center')
calibrateBtn.grid(row=4, column=1)
calibrateBtn.config(width=12, height=1)

# Pressure Sweep Widget
sweepButton = tk.Button(frame1, text='Pressure Sweep', command=threadedPressureSweep, anchor='center')
sweepButton.grid(row=5, column=1)
# sweepButton.config(state='disabled')
sweepButton.config(width=12, height=1)

# Set Pressure Widget
set = tk.Button(frame1, text="Set Pressure Settings", command=changeSweepSettings, anchor='center')
set.grid(row=3, column=1)
set.config(width=12, height=1)

# Export CSV Widget
exportBtn = tk.Button(frame1, text='Export CSV', command=exportCSV, anchor='center')
exportBtn.grid(row=3, column=0)
exportBtn.config(width=12, height=1)

# Reset Widget
resetBtn = tk.Button(frame1, text='Reset', command=reset, anchor='center')
resetBtn.grid(row=4, column=0)
resetBtn.config(width=12, height=1)

# Delete Widget
deleteBtn = tk.Button(frame1, text='Delete Sweep', command=delete, anchor='center')
deleteBtn.grid(row=5, column=0)
deleteBtn.config(width=12, height=1)

# Endoscope output
cap = cv2.VideoCapture(0)
if not cap.isOpened():
        updateOutput("Error: Could not open camera.")
        exit()

photo = None
def updateFrame():
    global photo
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        img = Image.fromarray(frame)
        img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
    win.after(15, updateFrame)  # Schedule the next frame update
def threadedUpdateFrame():
    threading.Thread(target=updateFrame).start()

canvas = tk.Canvas(frame1, width=30, height=70)
canvas.grid(row=6, column=0, columnspan=2, sticky="nsew")
threadedUpdateFrame()

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

presStartLabel = tk.Label(frame1, text='Starting Pressure (kPa)', width = 18, height = 1)
presIncrLabel = tk.Label(frame1, text='Pressure Increment (kPa)', width = 18, height = 1)
presNumIncrLabel = tk.Label(frame1, text='Number of Increments', width = 18, height = 1)
presStartLabel.grid(column=0, row=0, sticky="nsew")
presIncrLabel.grid(column=0, row=1, sticky="nsew")
presNumIncrLabel.grid(column=0, row=2, sticky="nsew")

# Notebook for graphs (to be used when graph is actually produced)
notebook = ttk.Notebook(win)

## Frame 2 Widgets

# Dynamic Text Outputs
o = tk.Label(frame2, text='Test Outputs')
o.grid(column=0, row=0, sticky="nsew")
def font_resize(event=None):
    x = o.winfo_width()
    y = o.winfo_height()
    if x < 20 or y < 30:  # guard clause to avoid tiny values
        return
    if x < y:
        o.config(font=("TkDefaultFont", (x-10)))
    elif y < 40:
        o.config(font=("TkDefaultFont", (y-20)))
    else:
        o.config(font=("TkDefaultFont", 20))

OutputLabel = ScrolledText(frame2, width=30, height=30, wrap=tk.WORD, relief=tk.RAISED, borderwidth=1)
OutputLabel.grid(column=0, row=1, sticky="nsew")

OutputLabel.insert(tk.END, long_text)
OutputLabel.configure(state = 'disabled')


win.bind('<Configure>', font_resize)
# win.bind("<Configure>", enforce_aspect)
win.mainloop()