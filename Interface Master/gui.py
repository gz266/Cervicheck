import tkinter as tk
from tkinter import *
import tkinter.ttk as ttk
import pandas as pd
import cv2
from PIL import Image, ImageTk
import threading

def updateOutput(long, OutputLabel):
    OutputLabel.configure(state='normal')
    OutputLabel.insert(tk.END, long)
    OutputLabel.see('end')
    OutputLabel.configure(state='disabled')
def updateParameters(A, C, Y, T, pads, a_label, C_label, youngs_label, time_label, pad_label, df, j):
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

def reset(win, OutputLabel, notebook, df, j):
    df = pd.DataFrame({'Pad number' : [1, 2, 3, 4, 5, 6, 7, 'α', 'C', 'Young\'s Modulus', 'Time (ms)']})
    notebook.destroy()
    notebook = ttk.Notebook(win)
    win.grid_columnconfigure(2, weight=0)
    OutputLabel.configure(state='normal')
    OutputLabel.delete(1.0, tk.END)
    OutputLabel.configure(state='disabled')
    j.set(1)

def exportCSV(df, OutputLabel):
    name = None
    name_var = tk.StringVar()
    def saveName(event=None):
        date = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
        name = field.get()
        if name == None:
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

    winput.mainloop()

def delete(j, df, notebook, win, OutputLabel):
    index = notebook.index("current")
    df.drop(df.columns[index+1], axis=1, inplace=True)
    notebook.forget(index)
    long_text = "\nSweep " + str(index + 1) + " deleted"
    updateOutput(long_text, OutputLabel)
    k = j.get()
    if k == 2:
        j.set(1)
        notebook.destroy()
        notebook = ttk.Notebook(win)
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
def threadedUpdateFrame(canvas, win, photo, cap):
    threading.Thread(target=updateFrame, args=(canvas, win, photo, cap)).start()

def callback(P):
        return str.isdigit(P) or P=='' or (str(P)[0] == '-' and str.isdigit(P[1:])) or str(P) == '-'

def font_resize(o, event=None):
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