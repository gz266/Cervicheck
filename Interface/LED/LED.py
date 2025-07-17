import tkinter as tk
from pyfirmata import Arduino

# Port to which Arduino is connected
commPort = '/dev/cu.usbmodem1101'

# Create board
board = Arduino(commPort)

# Create functions
def ledON():
    board.digital[13].write(1)
def ledOFF():
    board.digital[13].write(0)

# Root widget to create window
win = tk.Tk()

# Initialize window with title and minimum size in pixels (width x height)
win.title('LED')
win.minsize(200,60)

# Label widget
label = tk.Label(win, text='click to turn ON/OFF')
label.grid(column=1, row=1)

# Button widget
ONbtn = tk.Button(win, bd=4, text='LED ON', command=ledON)
ONbtn.grid(column=1, row=2)
OFFbtn = tk.Button(win, bd=4, text='LED OFF', command=ledOFF)
OFFbtn.grid(column=2,row=2)

# Start and open window continuously
win.mainloop()

