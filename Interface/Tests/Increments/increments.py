from tkinter import *
import tkinter as tk 
import serial
from time import sleep

commPort = '/dev/cu.usbmodem11201'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Function
def changeSweepSettings():
    ser.write(b'i')
    pres_start = presStart.get() + '\r'
    pres_incr = presIncr.get() + '\r'
    pres_num_incr = presNumIncr.get() + '\r'
    ser.write(pres_start.encode())
    sleep(0.1)
    ser.write(pres_incr.encode())
    sleep(0.1)
    ser.write(pres_num_incr.encode())
    sleep(0.1)


# Window
win = Tk() 
win.title('Edit Pressure Settings')
win.minsize(200,60)

# Entry widgets
presStart = tk.Entry(win, bd=6, width=8)
presStart.grid(column=0, row=0)
presIncr = tk.Entry(win, bd=6, width=8)
presIncr.grid(column=1, row=0)
presNumIncr = tk.Entry(win, bd=6, width=8)
presNumIncr.grid(column=2, row=0)

# Button widget
set = tk.Button(win, text="Set Pressure Settings", command=changeSweepSettings)
set.grid(row=0, column=3)

win.mainloop()