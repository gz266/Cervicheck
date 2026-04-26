from tkinter import *
import tkinter as tk 
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
import serial
from time import sleep
import json


#add parse the string into nested dictionary and display as pandas table


#if data is in json format
data = json.loads(line)




commPort = 'COM6'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

def read_serial():
    global running
    while running:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                # pass data to UI thread safely
                root.after(0, update_output, line)
        except Exception as e:
            root.after(0, update_output, f"Error: {e}")

def update_output(text):
    output.insert(tk.END, text + "\n")
    output.see(tk.END)


root = tk.Tk()
root.title("Impedance Dashboard")

def start_run():
    global running
    if not running:
        running = True
        ser.write(b's') 
        threading.Thread(target=read_serial, daemon=True).start()
        update_output("Started run")

start_button = tk.Button(root, text="Start", command=start_run)
start_button.pack()





output = ScrolledText(root, height=15, width=50)
output.pack()

root.mainloop()

