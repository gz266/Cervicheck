import tkinter as tk
from tkinter import *
from ScrollableNotebook import ScrollableNotebook
import pandas as pd
import cv2
from PIL import Image, ImageTk
import threading
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('agg')
import numpy as np
import communication
import config
from data_analysis import align_data, analyze_data, func, fit_calibration

def _ui(widget, fn):
    try:
        widget.after(0, fn)
    except tk.TclError:
        pass


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

    plot_canvas = live_plot_holder['plot_canvas']

    def apply():
        times = live_plot_holder['times']
        actual_pressures = live_plot_holder['actual_pressures']
        target_pressures = live_plot_holder['target_pressures']
        if not times:
            return

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

        plot_canvas.draw_idle()

    _ui(plot_canvas.get_tk_widget(), apply)


def markPressureContact(live_plot_holder, time_ms, pad_num, pressure, impedance):
    if live_plot_holder is None or live_plot_holder.get('plot_canvas') is None:
        return

    start_time_ms = live_plot_holder.get('start_time_ms')
    elapsed_s = 0 if start_time_ms is None else (time_ms - start_time_ms) / 1000.0

    plot_canvas = live_plot_holder['plot_canvas']

    def apply():
        marker_time = elapsed_s
        marker_pressure = pressure
        times = live_plot_holder.get('times', [])
        actual_pressures = live_plot_holder.get('actual_pressures', [])
        target_pressures = live_plot_holder.get('target_pressures', [])

        if times and actual_pressures:
            nearest_index = min(range(len(times)), key=lambda idx: abs(times[idx] - elapsed_s))
            marker_time = times[nearest_index]
            marker_pressure = actual_pressures[nearest_index]

        ax = live_plot_holder['ax']
        marker = ax.scatter([marker_time], [marker_pressure], s=35, c='black', zorder=5)
        live_plot_holder['contact_artists'].append(marker)

        all_times = times + [marker_time]
        all_pressures = actual_pressures + target_pressures + [marker_pressure]
        if all_times:
            ax.set_xlim(0, max(1.0, max(all_times)))
        if all_pressures:
            pressure_min = min(all_pressures)
            pressure_max = max(all_pressures)
            pressure_pad = max(1.0, (pressure_max - pressure_min) * 0.15)
            ax.set_ylim(pressure_min - pressure_pad, pressure_max + pressure_pad)

        status = live_plot_holder.get('status')
        if status is not None:
            status.config(text=f"Pad {pad_num} contact | Pressure {pressure:.2f} kPa | Impedance {impedance:.2f} ohms")

        plot_canvas.draw_idle()

    _ui(plot_canvas.get_tk_widget(), apply)


def updateOutput(long, OutputLabel):
    def _do():
        OutputLabel.configure(state='normal')
        OutputLabel.insert(tk.END, long)
        OutputLabel.see('end')
        OutputLabel.configure(state='disabled')
    try:
        OutputLabel.after(0, _do)
    except tk.TclError:
        pass
def updateParameters(A, C, E, Y, T, pads, a_label, C_label, eff_mod_label, youngs_mod_label, time_label, pad_label, df, j):
    if A < 0.001:
        formatted_A = '{:0.3e}'.format(A)
    else:
        formatted_A = '{:0.3f}'.format(A)
    if C > 9999:
        formatted_C = '{:0.3e}'.format(C)
    else:
        formatted_C = '{:0.3f}'.format(C)
    formatted_E = '{:0.3f}'.format(E)
    formatted_Y = '{:0.3f}'.format(Y)
    formatted_T = '{:0.0f}'.format(T)
    # pad_text = "Pad 1: " + str(pads[1]) + "\n\nPad 2: " + str(pads[2]) + "\n\nPad 3: " + str(pads[3]) + "\n\nPad 4: " + str(pads[4]) + "\n\nPad 5: " + str(pads[5]) + "\n\nPad 6: " + str(pads[6]) + "\n\nPad 7: " + str(pads[7])
    pad_text = "Pad 0: " + str(pads[1]) + "\n\nPad 1: " + str(pads[2]) + "\n\nPad 2: " + str(pads[3]) + "\n\nPad 3: " + str(pads[4]) + "\n\nPad 4: " + str(pads[5]) + "\n\nPad 5: " + str(pads[6]) + "\n\nPad 6: " + str(pads[7]) + "\n\nPad 7: " + str(pads[8])
    arr = [*pads[1:], formatted_A, formatted_C, formatted_E, formatted_Y, formatted_T]
    k = j.get()
    df.insert(df.shape[1], 'Sweep ' + str(k), arr)
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
    eff_mod_label.config(state='normal')
    eff_mod_label.delete(1.0, tk.END)
    eff_mod_label.insert(tk.END, "Effective modulus: ")
    eff_mod_label.insert(tk.END, formatted_E)
    eff_mod_label.config(state='disabled')
    youngs_mod_label.config(state='normal')
    youngs_mod_label.delete(1.0, tk.END)
    youngs_mod_label.insert(tk.END, "Young's modulus: ")
    youngs_mod_label.insert(tk.END, formatted_Y)
    youngs_mod_label.config(state='disabled')
    time_label.config(state='normal')
    time_label.delete(1.0, tk.END)
    time_label.insert(tk.END, "Time (ms): ")
    time_label.insert(tk.END, formatted_T)
    time_label.config(state='disabled')
    pad_label.config(state='normal')
    pad_label.delete(1.0, tk.END)
    pad_label.insert(tk.END, pad_text)
    pad_label.config(state='disabled')

def reset(win, OutputLabel, notebook_holder, df, j):
    notebook = notebook_holder['nb']
    # Row template comes from config so it always matches the width of the rows
    # that updateParameters() will insert. Spelling it out here is what let the
    # 7-pad and 8-pad versions drift apart.
    config.reset_dataframe(df)
    notebook.destroy()
    new_notebook = ScrollableNotebook(win, tabmenu = False)
    notebook_holder['nb'] = new_notebook 
    win.grid_columnconfigure(3, weight=0)
    OutputLabel.configure(state='normal')
    OutputLabel.delete(1.0, tk.END)
    OutputLabel.configure(state='disabled')
    j.set(1)

def exportCSV(df, OutputLabel):
    name = None
    name_var = tk.StringVar()
    def saveName(event=None):
        date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
        name = field.get().strip()
        # field.get() returns '' when empty, never None, so the old `== None`
        # check never fired and an empty box saved to a file called '.csv'.
        if not name:
            name = 'sweep_data_' + date
        name_var.set(name)
        long_text = "\nData exported to CSV file: " + name + ".csv"
        updateOutput(long_text, OutputLabel)
        name = name_var.get()
        df.to_csv(f'{name}.csv', index=False)
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

    field.focus_set()
    # wait_window() blocks on this dialog using the root's existing event loop.
    # mainloop() here would start a second, nested loop under the root's.
    winput.wait_window()

def delete(j, df, notebook_holder, win, OutputLabel):
    notebook = notebook_holder['nb']
    # No tabs at all (fresh start, post-reset, or the last sweep already deleted)
    # makes index("current") raise TclError rather than return anything useful.
    try:
        index = notebook.index("current")
    except tk.TclError:
        updateOutput("\nNo sweep to delete\n", OutputLabel)
        return
    df.drop(df.columns[index+1], axis=1, inplace=True)
    notebook.forget(index)
    long_text = "\nSweep " + str(index + 1) + " deleted"
    updateOutput(long_text, OutputLabel)
    k = j.get()
    if k == 2:
        j.set(1)
        notebook.destroy()
        new_notebook = ScrollableNotebook(win, tabmenu = False)
        notebook_holder['nb'] = new_notebook
        # Match reset(): the notebook is gone, so stop column 3 from claiming space.
        win.grid_columnconfigure(3, weight=0)
    else:
        for i in range(index, k-2):
            notebook.tab(i, text='Sweep ' + str(i+1))
            df.rename(columns={df.columns[i+1]: 'Sweep ' + str(i+1)}, inplace=True)
        j.set(k - 1)

# Endoscope output

def updateFrame(canvas, win, photo, cap):
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        img = Image.fromarray(frame)
        img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        win.after(15, lambda : updateFrame(canvas, win, photo, cap))  # Schedule the next frame update
    
class Pressure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return self.message


def changeSweepSettings(presStart, presIncr, presNumIncr, voltThresh, ser, OutputLabel):
    start = float(presStart.get())
    incr = float(presIncr.get())
    num_incr = int(presNumIncr.get())
    maxPres = start + incr * num_incr

    if start > 0:
        updateOutput("\nPressure must begin at 0 kPa or less", OutputLabel)
        raise Pressure("Pressure must begin at 0 kPa or less")
    elif maxPres < -50:
        updateOutput("\nPressure must be under 50 kPa", OutputLabel)
        raise Pressure("Pressure must be under 50 kPa")

    accepted, rejected = communication.applySweepSettings(
        ser, presStart.get(), presIncr.get(), presNumIncr.get(), voltThresh.get())

    updateOutput("\nSweep Settings Changed:"
                 f"\nStart: {presStart.get()}"
                 f"\nIncrement: {presIncr.get()}"
                 f"\nNumber of Increments: {presNumIncr.get()}\n", OutputLabel)

    if accepted is None:
        updateOutput("Contact Voltage: NO CONFIRMATION from device, threshold may be unchanged\n", OutputLabel)
    elif rejected is not None:
        updateOutput(f"Contact Voltage: REJECTED {rejected} V (must be 0-5 V), still using {accepted} V\n", OutputLabel)
    else:
        updateOutput(f"Contact Voltage: {accepted} V confirmed\n", OutputLabel)


def runCalibratePressure(ser, OutputLabel):
    def on_event(event):
        if event[0] == 'log':
            updateOutput(event[1], OutputLabel)
        elif event[0] == 'aborted':
            updateOutput(f"\nCalibration aborted: {event[1]}\n", OutputLabel)

    voltages, pressures = communication.readCalibration(ser, on_event)
    if voltages is None:
        return

    slope, intercept, r_squared = fit_calibration(pressures, voltages)
    updateOutput(f"Slope: {slope}\n", OutputLabel)
    updateOutput(f"Intercept: {intercept}\n", OutputLabel)
    updateOutput(f"R-Squared: {r_squared}\n", OutputLabel)
    communication.sendCalibration(ser, slope, intercept)


def threadedCalibratePressure(ser, OutputLabel):
    threading.Thread(target=runCalibratePressure, args=(ser, OutputLabel)).start()


def runCalibCheck(ser, OutputLabel):
    def on_event(event):
        if event[0] == 'log':
            updateOutput(event[1], OutputLabel)
        elif event[0] == 'aborted':
            updateOutput(f"\nCalib check: {event[1]}\n", OutputLabel)

    communication.calibCheck(ser, on_event)


def runPressureSweep(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder=None, k=1):
    cap.release()
    notebook = notebook_holder['nb']

    def on_event(event):
        kind = event[0]
        if kind == 'pressure':
            updateLivePressurePlot(live_plot_holder, *event[1:])
        elif kind == 'contact':
            markPressureContact(live_plot_holder, *event[1:])
        elif kind == 'log':
            updateOutput(event[1], OutputLabel)
        elif kind == 'aborted':
            updateOutput(f"\nSweep aborted: {event[1]}\n", OutputLabel)

    pads, elapsed_ms = communication.pressureSweep(ser, on_event)

    if pads is not None:
        x, y = align_data(strain, pads)
        coefficients, eff_mod, youngs_mod, _ = analyze_data(x, y)

        def build(x=x, y=y, coefficients=coefficients, eff_mod=eff_mod,
                  youngs_mod=youngs_mod, elapsed=elapsed_ms, pads=pads.copy()):
            fig, ax = plt.subplots(figsize=(3, 2), layout='constrained')
            strain_min, strain_max = 1.0, 2.5
            ax.set_xlim([strain_min, strain_max])
            ax.set_title("Stress Strain Curve")
            ax.set_ylabel("Pressure (kPa)")
            ax.set_xlabel("Strain Ratio")

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
            curve_x = np.linspace(strain_min, strain_max, 300)
            ax.plot(curve_x, func(curve_x, *coefficients), 'r-')
            youngs_mod_line = lambda v: youngs_mod * v - youngs_mod
            ax.plot(curve_x, youngs_mod_line(curve_x), 'g--')
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

            updateParameters(*coefficients, eff_mod, youngs_mod, elapsed, pads, a_label, C_label, eff_mod_label, youngs_mod_label, time_label, pad_label, df, j)

            notebook.select(k-1)
            j.set(k+1)

        _ui(win, build)

    _ui(btn, lambda: btn.config(text="Open Camera", command=lambda: openCamera(canvas, win, OutputLabel, btn, ser, strain, j, df, notebook_holder, live_plot_holder)))


def threadedPressureSweep(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder=None):
    setupLivePressurePlot(live_plot_holder)
    k = j.get()
    threading.Thread(target=runPressureSweep,
                     args=(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder),
                     kwargs={'k': k}).start()


def openCamera(canvas, win, OutputLabel, btn, ser, strain, j, df, notebook_holder, live_plot_holder=None):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        updateOutput("Error: Could not open camera.", OutputLabel)
    photo = None
    updateFrame(canvas, win, photo, cap)
    btn.config(text="Pressure Sweep", command=lambda: threadedPressureSweep(win, ser, strain, j, df, notebook_holder, OutputLabel, cap, canvas, btn, live_plot_holder))

def callback(P):
    try:
        float(P)
        return True
    except ValueError:
        return False
    return str.isdigit(P) or P=='' or (str(P)[0] == '-' and str.isdigit(P[1:])) or str(P) == '-'

def font_resize(o, event=None):
        x = o.winfo_width()
        y = o.winfo_height()
        if x < 20 or y < 30:  # guard clause to avoid tiny values
            return
        if x < y:
            size = x - 10
        elif y < 40:
            size = y - 20
        else:
            size = 20
        if getattr(o, '_last_font_size', None) == size:
            return
        o._last_font_size = size
        o.config(font=("TkDefaultFont", size))

def bind_font_resize(win, o, delay=120):
    pending = {'id': None}
    def on_configure(event=None):
        if pending['id'] is not None:
            try:
                win.after_cancel(pending['id'])
            except tk.TclError:
                pass
        pending['id'] = win.after(delay, lambda: font_resize(o=o))
    win.bind('<Configure>', on_configure)