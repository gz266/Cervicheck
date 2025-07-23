import tkinter as tk
from tkinter import messagebox
from pyfirmata import Arduino, PWM
from time import sleep

# Functions
def blueLED():
    delay = float(LEDtime.get())
    brightness = float(LEDbright.get())
    blueBtn.config(state = tk.DISABLED)
    board.digital[5].write(brightness/100.0)
    sleep(delay)
    board.digital[5].write(0)
    blueBtn.config(state = tk.ACTIVE)

def redLED():
    delay = float(LEDtime.get())
    brightness = float(LEDbright.get())
    redBtn.config(state = tk.DISABLED)
    board.digital[3].write(brightness/100.0)
    sleep(delay)
    board.digital[3].write(0)
    redBtn.config(state = tk.ACTIVE)

def aboutMsg():
    messagebox.showinfo('About', "Logic Don't Care Software\nLED Control Ver 1.0\nAugust 2022")

# Port to which Arduino is connected
commPort = '/dev/cu.usbmodem1101'

# Create board
board = Arduino(commPort)

# Set pin modes to PWM
# Use pins 3 and 5 since those are PWM
board.digital[3].mode = PWM
board.digital[5].mode = PWM

# Root widget to create window
win = tk.Tk()

# Initialize window with title and minimum size in pixels (width x height)
win.title('LED Control')
win.minsize(235,150)

# Entry widget
LEDtime = tk.Entry(win, bd=6, width=8)
LEDtime.grid(column=1, row=1)
# Label widget
tk.Label(win, text='LED ON Time (sec)').grid(column=2, row=1)

# Scale widget
LEDbright = tk.Scale(win, bd=5, from_=0, to=100, orient=tk.HORIZONTAL)
LEDbright.grid(column=1, row=2)
# Label widget
tk.Label(win, text='LED Brightness (%)').grid(column=2, row=2)

# Button widgets
blueBtn = tk.Button(win, bd=5, text='Blue LED', command=blueLED)
blueBtn.grid(column=1, row=3)

redBtn = tk.Button(win, bd=5, text='Red LED', command = redLED)
redBtn.grid(column=2, row=3)

aboutBtn = tk.Button(win, text='About', command=aboutMsg)
aboutBtn.grid(column=1, row=4)

quitBtn = tk.Button(win, text='Quit', command=win.quit)
quitBtn.grid(column=2, row=4)

win.mainloop()