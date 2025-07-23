import matplotlib.pyplot as plt
import tkinter as tk
 
# Initialize Tkinter
root = tk.Tk()
 
# Tkinter Application
frame = tk.Frame(root)
label = tk.Label(text = "Matplotlib + Tkinter!")
label.config(font=("Courier", 32))
label.pack()
frame.pack()
 
root.mainloop()