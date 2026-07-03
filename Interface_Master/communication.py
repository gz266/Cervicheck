import serial
import scipy
import threading
from time import sleep
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import *
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation
matplotlib.use('agg')
import cv2
from data_analysis import align_data, analyze_data, func
from gui import updateOutput, updateParameters, threadedUpdateFrame, openCamera


def setupLivePressurePlot(live_plot_holder):
    if live_plot_holder is None:
        return

    parent = live_plot_holder.get('parent')
    if parent is None:
        return

    old_fig = live_plot_holder.get('fig')
    if old_fig is not None:
        plt.close(old_fig)

    for child in parent.winfo_children():
        child.destroy()

    fig, ax = plt.subplots(figsize=(3, 2), layout='constrained')
    actual_line, = ax.plot([], [], 'b-', label='Measured')
    target_line, = ax.plot([], [], 'r--', label='Target')

    ax.set_title("Live Pressure")
    ax.set_ylabel("Pressure (kPa)")
    ax.set_xlabel("Time (s)")
    ax.grid(True, linestyle='--', linewidth=0.5)
    ax.legend(loc='best')

    plot_canvas = FigureCanvasTkAgg(fig, master=parent)
    plot_canvas.get_tk_widget().grid(row=0, column=0, sticky="NSEW")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

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
        status.config(text="Live pressure: waiting for samples")


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

    times = live_plot_holder['times']
    actual_pressures = live_plot_holder['actual_pressures']
    target_pressures = live_plot_holder['target_pressures']

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
        status.config(text=f"Pad {pad_num} | Target {target_pressure:.2f} kPa | Measured {actual_pressure:.2f} kPa")

    live_plot_holder['plot_canvas'].draw_idle()


def markPressureContact(live_plot_holder, time_ms, pad_num, pressure, impedance):
    if live_plot_holder is None or live_plot_holder.get('plot_canvas') is None:
        return

    start_time_ms = live_plot_holder.get('start_time_ms')
    elapsed_s = 0 if start_time_ms is None else (time_ms - start_time_ms) / 1000.0

    ax = live_plot_holder['ax']
    marker = ax.scatter([elapsed_s], [pressure], s=35, c='black', zorder=5)
    live_plot_holder['contact_artists'].append(marker)

    status = live_plot_holder.get('status')
    if status is not None:
        status.config(text=f"Pad {pad_num} contact | Pressure {pressure:.2f} kPa | Impedance {impedance:.2f} ohms")

    live_plot_holder['plot_canvas'].draw_idle()


def parsePressureLine(data):
    parts = data.strip().split(',')
    if len(parts) != 5:
        return None

    try:
        return float(parts[1]), float(parts[2]), float(parts[3]), int(parts[4])
    except ValueError:
        return None


def parseContactLine(data):
    parts = data.strip().split(',')
    if len(parts) != 5:
        return None

    try:
        return float(parts[1]), int(parts[2]), float(parts[3]), float(parts[4])
    except ValueError:
        return None


def calibratePressure(ser, OutputLabel):
    ser.write(b'p')
    voltage = []
    pressure = []
    v_b = False
    p_b = False
    i = 0
    while True:
        data = ser.readline().decode('ascii')
        updateOutput(data, OutputLabel)
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
    updateOutput('Slope: '+ slope, OutputLabel)
    updateOutput('Intercept: '+ intercept, OutputLabel)
    updateOutput('R-Squared: ' + r_squared, OutputLabel)
    ser.write(slope.encode())   
    sleep(0.1)
    ser.write(intercept.encode())
    sleep(0.1)
    # sweepButton.config(state='normal')

def pressureSweep(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder=None):
    cap.release()
    notebook = notebook_holder['nb']
    setupLivePressurePlot(live_plot_holder)
    ser.write(b's') 
    b = False
    pressure = np.zeros(8)
    k = j.get()
    while True:
        data = ser.readline().decode('ascii')
        if data.startswith("PRESSURE,"):
            parsed = parsePressureLine(data)
            if parsed is not None:
                updateLivePressurePlot(live_plot_holder, *parsed)
            continue
        if data.startswith("CONTACT,"):
            parsed = parseContactLine(data)
            if parsed is not None:
                markPressureContact(live_plot_holder, *parsed)
            continue
        updateOutput(data, OutputLabel)
        if data.startswith("Done"):
            b = True
            i = 0
        if data.startswith("Time"):
            time = float(data[6:])
            # try:
            x, y = align_data(strain, pressure)
            coefficients, eff_mod, youngs_mod, intercept = analyze_data(x, y)
            fig, ax = plt.subplots(figsize=(3, 2), layout='constrained')
            ax.set_ylim([0, 10])                              # Set Y axis limit of plot
            ax.set_xlim([1, 2])  
            ax.set_title("Stress Strain Curve")                        # Set title of figure
            ax.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
            ax.set_xlabel("Percent Strain (%)")         # Set title of x axis

            if k == 1:
                notebook.grid(column=3, row=0, sticky='NSEW')
                win.grid_columnconfigure(3, weight=1)
                notebook.grid_rowconfigure(0, weight=1)
                notebook.grid_columnconfigure(0, weight=1)
            graph = tk.Frame()
            notebook.add(graph, text = 'Sweep ' + str(k))
            graph.grid_rowconfigure(0, weight=1)
            graph.grid_columnconfigure(0, weight=1)
            graph.grid_columnconfigure(1, weight=1)
            canvas_new = FigureCanvasTkAgg(fig, master=graph)
            canvas_widget_new = canvas_new.get_tk_widget()
            canvas_widget_new.grid(row=0, column=0, columnspan=2, sticky="NSEW")
            canvas_widget_new.grid_rowconfigure(0, weight=1)
            canvas_widget_new.grid_columnconfigure(0, weight=1)
            ax.plot(x, func(x, *coefficients), 'r-')
            youngs_mod_line = lambda x: youngs_mod * x - youngs_mod
            ax.plot(x, youngs_mod_line(x), 'g--')
            ax.scatter(x, -y, s=4, c='black')
            canvas_new.draw()

            a_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
            a_label.grid(column=0, row=5, sticky="nsew")
            a_label.config(state='disabled')
            C_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
            C_label.grid(column=0, row=6, sticky="nsew")
            C_label.config(state='disabled')
            eff_mod_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
            eff_mod_label.grid(column=0, row=7, sticky="nsew")
            eff_mod_label.config(state='disabled')
            youngs_mod_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
            youngs_mod_label.grid(column=0, row=8, sticky="nsew")
            youngs_mod_label.config(state='disabled')
            time_label = tk.Text(graph, height=3, width=30, relief=tk.RAISED, borderwidth=1)
            time_label.grid(column=0, row=9, sticky="nsew")
            time_label.config(state='disabled')
            pad_label = tk.Text(graph, height=15, width=30, relief=tk.RAISED, borderwidth=1)
            pad_label.grid(column=1, row=5, rowspan=5, sticky="nsew")
            pad_label.config(state='disabled')

            updateParameters(*coefficients, eff_mod, youngs_mod, time, pressure, a_label, C_label, eff_mod_label, youngs_mod_label, time_label, pad_label, df, j)

            notebook.select(k-1)
            j.set(k+1)
            # except:
            #     updateOutput("No pads were contacted\n", OutputLabel)
            break
        if b:
            if i == 0:
                i = i + 1
            else:
                data_float = float(data)
                pressure[i] = data_float
                i = i + 1
    btn.config(text="Open Camera", command=lambda: openCamera(canvas, win, OutputLabel, btn, ser, strain, j, df, notebook_holder, live_plot_holder))
    

def changeSweepSettings(presStart, presIncr, presNumIncr, impThresh, ser, OutputLabel):
    maxPres = float(presStart.get()) + float(presIncr.get()) * int(presNumIncr.get())
    if float(presStart.get()) > 0:
        long_text = "\nPressure must begin at 0 kPa or less"
        updateOutput(long_text, OutputLabel)
        raise Pressure("Pressure must begin at 0 kPa or less")
    elif maxPres < -50:
        long_text = "\nPressure must be under 50 kPa"
        updateOutput(long_text, OutputLabel)
        raise Pressure("Pressure must be under 50 kPa")
    ser.write(b'i')
    pres_start = presStart.get() + '\r'
    pres_incr = presIncr.get() + '\r'
    pres_num_incr = presNumIncr.get() + '\r'
    imp_thresh = impThresh.get() + '\r'
    ser.write(pres_start.encode())
    sleep(0.1)
    ser.write(pres_incr.encode())
    sleep(0.1)
    ser.write(pres_num_incr.encode())
    sleep(0.1)
    ser.write(imp_thresh.encode())
    sleep(0.1)
    long_text = "\nSweep Settings Changed:\nStart: " + pres_start + "Increment: " + pres_incr + "Number of Increments: " + pres_num_incr + "Impedance Threshold: " + imp_thresh
    updateOutput(long_text, OutputLabel)

def threadedCalibratePressure(ser, OutputLabel):
    threading.Thread(target=calibratePressure, args=(ser, OutputLabel)).start()
def threadedPressureSweep(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder=None):
    threading.Thread(target=pressureSweep, args=(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder)).start()

# Exception
class Pressure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"
