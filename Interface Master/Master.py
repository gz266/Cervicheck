from time import sleep
import serial
import threading
import tkinter as tk
from tkinter import *
import tkinter.ttk as ttk
import cv2
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import pandas as pd
import numpy as np
from communication import threadedCalibratePressure, threadedPressureSweep, changeSweepSettings
from gui import updateOutput, reset, exportCSV, delete, threadedUpdateFrame, updateFrame

def main():
    commPort = '/dev/cu.usbmodem11201'
    ser = serial.Serial(commPort, baudrate = 9600)
    sleep(2)

    strain = np.array([1, 1.2415, 1.406, 1.572, 1.738, 1.9045, 2.071, 2.2375])

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

    j = tk.IntVar(value=1)

    ## Frame 1 Widgets

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

    # Buttons
    # Calibrate widget
    calibrateBtn = tk.Button(frame1, text='Calibrate Pressure', command=lambda: threadedCalibratePressure(ser, OutputLabel), anchor='center')
    calibrateBtn.grid(row=4, column=1)
    calibrateBtn.config(width=12, height=1)

    # Pressure Sweep Widget
    sweepButton = tk.Button(frame1, text='Pressure Sweep', command=lambda: threadedPressureSweep(win, ser, strain, j, df, notebook, OutputLabel), anchor='center')
    sweepButton.grid(row=5, column=1)
    # sweepButton.config(state='disabled')
    sweepButton.config(width=12, height=1)

    # Set Pressure Widget
    set = tk.Button(frame1, text="Set Pressure Settings", command=lambda : changeSweepSettings(presStart, presIncr, presNumIncr, ser, OutputLabel), anchor='center')
    set.grid(row=3, column=1)
    set.config(width=12, height=1)

    # Export CSV Widget
    exportBtn = tk.Button(frame1, text='Export CSV', command=lambda : exportCSV(df, OutputLabel), anchor='center')
    exportBtn.grid(row=3, column=0)
    exportBtn.config(width=12, height=1)

    # Reset Widget
    resetBtn = tk.Button(frame1, text='Reset', command= lambda: reset(win, OutputLabel, notebook, df, j), anchor='center')
    resetBtn.grid(row=4, column=0)
    resetBtn.config(width=12, height=1)

    # Delete Widget
    deleteBtn = tk.Button(frame1, text='Delete Sweep', command=lambda : delete(j, df, notebook, win, OutputLabel), anchor='center')
    deleteBtn.grid(row=5, column=0)
    deleteBtn.config(width=12, height=1)

    canvas = tk.Canvas(frame1, width=30, height=70)
    canvas.grid(row=6, column=0, columnspan=2, sticky="nsew")

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

    OutputLabel.configure(state = 'disabled')

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
            updateOutput("Error: Could not open camera.", OutputLabel)
            exit()
    photo = None
    updateFrame(canvas, win, photo, cap)

    win.bind('<Configure>', font_resize)
    win.mainloop()

if __name__ == "__main__":
    main()