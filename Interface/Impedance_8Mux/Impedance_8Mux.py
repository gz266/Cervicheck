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


commPort = '/dev/cu.usbmodem1101'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

def changeSweepSettings():
    ser.write(b'o')
    global Start_Freq, Freq_Incr, Num_Incr, Ref_Res
    startFreq = Start_Freq.get() + '\r'
    freqIncr = Freq_Incr.get() + '\r'
    numIncr = Num_Incr.get() + '\r'
    refRes = Ref_Res.get() + '\r'
    ser.write(startFreq.encode())
    sleep(0.1)
    ser.write(freqIncr.encode())
    sleep(0.1)
    ser.write(numIncr.encode())
    sleep(0.1)
    ser.write(refRes.encode())
    sleep(0.1)
    long_text = "Impedance Settings Changed:\nStart Frequency: " + startFreq.strip('\r') + "(Hz)" + "\nFrequency Increment: " + freqIncr.strip('\r') + " (Hz)" + "\nNumber of Increments: " + numIncr.strip('\r') + "\nReference Resistance: " + refRes.strip('\r') + " (Ohms)"
    updateOutput(long_text)

def frequencySweep():
    ser.write(b'p')
    frequency = [] 
    impedance = []
    phase = []
    k = j.get()
    while True:
        data = ser.readline().decode('ascii')
        # print(data)
        updateOutput(data)
        if data.startswith('Frequency sweep'):
            break
        if data.startswith('Frequency'):
            frequency.append(float(data.split(':')[1].strip()))
        if data.startswith('Impedance'):
            impedance.append(float(data.split(':')[1].strip()))
        if data.startswith('Phase'):
            phase.append(float(data.split(':')[1].strip()))
    
        # if i > 0:
        #     impedance.append(float(data.strip(':').split('=')[1]))
        #     frequency.append(int(data.split(':')[0])) 
        # if data.startswith('Performing'):
        #     i = 1
    if k == 1:
        notebook.grid(column=1, row=0, sticky='NSEW')
        win.grid_columnconfigure(2, weight=1)
        notebook.grid_rowconfigure(0, weight=1)
        notebook.grid_columnconfigure(0, weight=1)
    fig_imp, ax_imp = plt.subplots(figsize=(3, 2), layout='constrained')
    min_imp = min(impedance) - 1000 if min(impedance) - 1000 >= 0 else 0
    max_imp = max(impedance) + 1000
    ax_imp.set_ylim(min_imp, max_imp)                             # Set Y axis limit of plot
    ax_imp.set_xlim(min(frequency), max(frequency))  
    ax_imp.set_title("Impedance Bode Plot")                        # Set title of figure
    ax_imp.set_ylabel("Impedance (Ohms)")                              # Set title of y axis 
    ax_imp.set_xlabel("Frequency (kHz)")         # Set title of x axis
    ax_imp.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(10))
    ax_imp.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax_imp.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax_imp.plot(frequency, impedance, 'o-', color='black')  # Plot impedance vs frequency
    graph = tk.Frame()
    canvas_imp = FigureCanvasTkAgg(fig_imp, master=graph)
    canvas_imp.draw()
    notebook.add(graph, text = 'Frequency Sweep ' + str(k))
    graph.grid_rowconfigure(0, weight=1)
    graph.grid_columnconfigure(0, weight=1)
    graph.grid_columnconfigure(1, weight=1)
    canvas_imp.get_tk_widget().grid(row=0, column=0, sticky='NSEW')

    fig_phase, ax_phase = plt.subplots(figsize=(3, 2), layout='constrained')
    ax_phase.set_ylim(-180, 180)
    ax_phase.set_xlim(min(frequency), max(frequency))
    ax_phase.set_title("Phase Bode Plot")                        # Set title of figure
    ax_phase.set_ylabel("Phase (Degrees)")                              # Set title of y axis 
    ax_phase.set_xlabel("Frequency (kHz)")         # Set title of x axis
    ax_phase.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(10))
    ax_phase.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax_phase.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax_phase.plot(frequency, phase, 'o-', color='black')  # Plot phase vs frequency
    canvas_phase = FigureCanvasTkAgg(fig_phase, master=graph)
    canvas_phase.draw()
    canvas_phase.get_tk_widget().grid(row=1, column=0, sticky='NSEW')

    notebook.select(len(notebook.tabs())-1)
    j.set(k + 1)
    


def selectPad():
    ser.write(b's')
    pad_num = Pad.get() + '\r'
    ser.write(pad_num.encode())
    sleep(0.1)
    long_text = "Pad " + pad_num.strip('\r') + " Selected\n"
    updateOutput(long_text)
    
def updateOutput(long):
    OutputLabel.insert(tk.END, long)
    OutputLabel.see('end')

long_text = ""

win = Tk() 
j = tk.IntVar(value=1)
frame1 = tk.Frame(win, relief=tk.RAISED, borderwidth=1)
frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame3 = tk.Frame(win, relief=tk.RAISED, borderwidth=1) 
frame3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

# Dynamic Text Outputs
o = tk.Label(frame3, text='Test Outputs')
o.grid(column=0, row=0, sticky="nsew")

OutputLabel = ScrolledText(frame3, width=60, height=30, wrap=tk.WORD, relief=tk.RAISED, borderwidth=1)
OutputLabel.grid(column=0, row=1, sticky="nsew")

OutputLabel.insert(tk.END, long_text)

win.title('Impedance Measurement Interface')
win.minsize(200,60)


# Entry widgets
def callback(P):
    return str.isdigit(P) or P=='' or (str(P)[0] == '-' and str.isdigit(P[1:])) or str(P) == '-'
vcmd = (win.register(callback))

# Widgets

calibrateImpedance = tk.Button(frame1, text='Calibrate Impedance', command=lambda : changeSweepSettings())
calibrateImpedance.grid(row=5, column=1)

impedanceSweep = tk.Button(frame1, text='Impedance Sweep', command=lambda : frequencySweep())
impedanceSweep.grid(row=6, column=1)

testButton = tk.Button(frame1, text='Test Resistance', command=lambda : frequencySweep())
testButton.grid(row=8, column=1)

setPad = tk.Button(frame1, text='Select Pad', command=lambda : selectPad())
setPad.grid(row=10, column=1)

# Entry

Start_Freq = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
Freq_Incr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
Num_Incr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
Ref_Res = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
Pad = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))


Start_Freq.insert(0, "10000")
Freq_Incr.insert(0, "5000")
Num_Incr.insert(0, "5")
Ref_Res.insert(0, "300")
Pad.insert(0, "0")

Start_Freq.grid(column=1, row=0, sticky="nsew")
Freq_Incr.grid(column=1, row=1, sticky="nsew")
Num_Incr.grid(column=1, row=2, sticky="nsew")
Ref_Res.grid(column=1, row=3, sticky="nsew")
Pad.grid(column=1, row=9, sticky="nsew")

presStartLabel = tk.Label(frame1, text='Starting Frequency (kHz)')
presIncrLabel = tk.Label(frame1, text='Frequency Increment (kHz)')
presNumIncrLabel = tk.Label(frame1, text='Number of Increments')
refResLabel = tk.Label(frame1, text='Reference Resistance (Ohms)')
testResLabel = tk.Label(frame1, text='Test Resistance (Ohms)')

presStartLabel.grid(column=0, row=0, sticky="nsew")
presIncrLabel.grid(column=0, row=1, sticky="nsew")
presNumIncrLabel.grid(column=0, row=2, sticky="nsew")
refResLabel.grid(column=0, row=3, sticky="nsew")
testResLabel.grid(column=0, row=7, sticky="nsew")

# Notebook for graphs (to be used when graph is actually produced)
notebook = ttk.Notebook(win)

win.mainloop()