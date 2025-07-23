import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
     FigureCanvasTkAgg)
import matplotlib.animation as animation
import tkinter as tk
import numpy as np
from tkinter import *
import time
import serial
 
def animate(i, dataList, ser):
    ser.write(b'g')                                     # Transmit the char 'g' to receive the Arduino data point
    arduinoData_string = ser.readline().decode('ascii') # Decode receive Arduino data as a formatted string
    #print(i)                                           # 'i' is a incrementing variable based upon frames = x argument

    try:
        arduinoData_float = float(arduinoData_string)   # Convert to float
        dataList.append(arduinoData_float)              # Add to the list holding the fixed number of points to animate

    except:                                             # Pass if data point is bad                               
        pass

    dataList = dataList[-50:]                           # Fix the list size so that the animation plot 'window' is x number of points
    
    ax.clear()                                          # Clear last data frame
    ax.plot(dataList)                                   # Plot new data frame
    
    ax.set_ylim([-50, 5])                              # Set Y axis limit of plot
    ax.set_title("Pressure Plot")                        # Set title of figure
    ax.set_ylabel("Pressure (kPa)")                              # Set title of y axis 
    ax.get_xaxis().set_visible(False)

dataList = []                                           # Create empty list variable for later use

# Initialize Tkinter and Matplotlib Figure
root = tk.Tk()
fig, ax = plt.subplots()
 
# Tkinter Application
frame = tk.Frame(root)
root.title('Pressure Grapher')
frame.pack()
 
# Create Canvas
canvas = FigureCanvasTkAgg(fig, master=root)  
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
 
# Plot data on Matplotlib Figure
commPort = '/dev/cu.usbmodem1101'
ser = serial.Serial(commPort, baudrate = 9600)          # Establish Serial object with COM port and BAUD rate to match Arduino Port/rate
time.sleep(2)                                           # Time delay for Arduino Serial initialization 

                                                        # Matplotlib Animation Fuction that takes takes care of real time plot.
                                                        # Note that 'fargs' parameter is where we pass in our dataList and Serial object. 
ani = animation.FuncAnimation(fig, animate, frames=100, fargs=(dataList, ser), interval=100) 
canvas.draw()
 
root.mainloop()
ser.close()                                             # Close Serial connection when plot is closed