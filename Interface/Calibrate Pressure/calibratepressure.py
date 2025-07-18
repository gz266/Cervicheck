from tkinter import *
import tkinter as tk 
import serial
from time import sleep

commPort = '/dev/cu.usbmodem1101'
ser = serial.Serial(commPort, baudrate = 9600)
sleep(2)

# Function
def calibratePressure():
    ser.write(b'p')

# Window
win = Tk() 
win.title('Calibrate GUI')
win.minsize(200,60)

calibrateBtn = tk.Button(win, text='Calibrate', command=calibratePressure)
calibrateBtn.grid(row=0, column=0)

win.mainloop()