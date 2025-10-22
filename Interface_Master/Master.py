from time import sleep
import serial
import tkinter as tk
from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
from ScrollableNotebook import ScrollableNotebook
import pandas as pd
import numpy as np
from communication import threadedCalibratePressure, threadedPressureSweep, changeSweepSettings
from gui import updateOutput, reset, exportCSV, delete, threadedUpdateFrame, updateFrame, font_resize, callback, openCamera

def main():
    commPort = '/dev/cu.usbmodem101'
    ser = serial.Serial(commPort, baudrate = 9600)
    sleep(2)

    strain = np.array([1, 1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65])

    # Pandas dataframe to hold all data
    data = {'Pad number' : [1, 2, 3, 4, 5, 6, 7, 'α', 'C', 'Effective Modulus', 'Young\'s Modulus', 'Time (ms)']}
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
    frame1.grid_rowconfigure(7, weight=1)

    frame2.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")
    frame2.grid_rowconfigure(0, weight=1)
    frame2.grid_columnconfigure(0, weight=1)
    frame2.grid_rowconfigure(1, weight=1)

    win.title('Stress Strain Testing')
    win.minsize(200,60)

    j = tk.IntVar(value=1)

    ## Frame 1 Widgets

    # Entry widgets
    vcmd = (win.register(callback))

    presStart = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
    presIncr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
    presNumIncr = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))
    impThresh = tk.Entry(frame1, bd=6, width=8, validate='key', validatecommand=(vcmd, '%P'))

    presStart.insert(0, "-1")
    presIncr.insert(0, "-1")
    presNumIncr.insert(0, "20")
    impThresh.insert(0, "500")
    presStart.grid(column=1, row=0, sticky="nsew")
    presIncr.grid(column=1, row=1, sticky="nsew")
    presNumIncr.grid(column=1, row=2, sticky="nsew")
    impThresh.grid(column=1, row=3, sticky="nsew")

    presStartLabel = tk.Label(frame1, text='Starting Pressure (kPa)', width = 18, height = 1)
    presIncrLabel = tk.Label(frame1, text='Pressure Increment (kPa)', width = 18, height = 1)
    presNumIncrLabel = tk.Label(frame1, text='Number of Increments', width = 18, height = 1)
    impThreshLabel = tk.Label(frame1, text='Impedance Threshold', width = 18, height = 1)
    presStartLabel.grid(column=0, row=0, sticky="nsew")
    presIncrLabel.grid(column=0, row=1, sticky="nsew")
    presNumIncrLabel.grid(column=0, row=2, sticky="nsew")
    impThreshLabel.grid(column=0, row=3, sticky="nsew")

    # Buttons
    # Calibrate widget
    calibrateBtn = tk.Button(frame1, text='Calibrate Pressure', command=lambda: threadedCalibratePressure(ser, OutputLabel), anchor='center')
    calibrateBtn.grid(row=5, column=1)
    calibrateBtn.config(width=12, height=1)

    # Pressure Sweep Widget
    sweepButton = tk.Button(frame1, text='Open Camera', command=lambda: openCamera(canvas, win, OutputLabel, sweepButton, ser, strain, j, df, notebook_holder), anchor='center')
    sweepButton.grid(row=6, column=1)
    # sweepButton.config(state='disabled')
    sweepButton.config(width=12, height=1)
    sweepButton.config()

    # Set Pressure Widget
    set = tk.Button(frame1, text="Set Sweep Settings", command=lambda : changeSweepSettings(presStart, presIncr, presNumIncr, impThresh, ser, OutputLabel), anchor='center')
    set.grid(row=4, column=1)
    set.config(width=12, height=1)

    # Export CSV Widget
    exportBtn = tk.Button(frame1, text='Export CSV', command=lambda : exportCSV(df, OutputLabel), anchor='center')
    exportBtn.grid(row=4, column=0)
    exportBtn.config(width=12, height=1)

    # Reset Widget
    resetBtn = tk.Button(frame1, text='Reset', command= lambda: reset(win, OutputLabel, notebook_holder, df, j), anchor='center')
    resetBtn.grid(row=5, column=0)
    resetBtn.config(width=12, height=1)

    # Delete Widget
    deleteBtn = tk.Button(frame1, text='Delete Sweep', command=lambda : delete(j, df, notebook_holder, win, OutputLabel), anchor='center')
    deleteBtn.grid(row=6, column=0)
    deleteBtn.config(width=12, height=1)

    canvas = tk.Canvas(frame1, width=30, height=70)
    canvas.grid(row=7, column=0, columnspan=2, sticky="nsew")

    # Notebook for graphs (to be used when graph is actually produced)
    notebook = ScrollableNotebook(win, tabmenu = False)
    notebook_holder = {}
    notebook_holder['nb'] = notebook

    ## Frame 2 Widgets

    # Dynamic Text Outputs
    o = tk.Label(frame2, text='Test Outputs')
    o.grid(column=0, row=0, sticky="nsew")

    OutputLabel = ScrolledText(frame2, width=30, height=30, wrap=tk.WORD, relief=tk.RAISED, borderwidth=1)
    OutputLabel.grid(column=0, row=1, sticky="nsew")

    OutputLabel.configure(state = 'disabled')

    

    win.bind('<Configure>', lambda event: font_resize(o=o))
    win.mainloop()

if __name__ == "__main__":
    main()