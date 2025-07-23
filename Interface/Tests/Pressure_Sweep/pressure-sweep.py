from tkinter import *
import tkinter as tk 
import serial
from time import sleep


commPort = '/dev/cu.usbmodem11201'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Function
def pressureSweep():
    ser.write(b's')

# Window
win = tk.Tk()
win.title('Pressure Sweep GUI')
win.minsize(200,60)

# Button widget
sweepButton = tk.Button(win, text='Pressure Sweep', command=pressureSweep)
sweepButton.grid(row=0, column=0)

win.mainloop()