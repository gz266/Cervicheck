import cv2
import tkinter as tk
from tkinter import *
from PIL import Image
from PIL import ImageTk
import threading

cap = cv2.VideoCapture(0)
if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()
print("Resolution:", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "x", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

photo = None  # global reference to image so it doesn't get garbage collected
ASPECT_RATIO = 1920./1080.  # Width / Height

def enforce_aspect(event):
    # This callback runs whenever the window is resized
    desired_width = int(event.height * ASPECT_RATIO)
    desired_height = int(event.width / ASPECT_RATIO)

    # Pick the limiting dimension (width or height)
    if desired_width <= event.width:
        win.geometry(f"{desired_width}x{event.height}")
    else:
        win.geometry(f"{event.width}x{desired_height}")


def update_frame():
    global photo
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        img = Image.fromarray(frame)
        img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
    win.after(15, update_frame)  # Schedule the next frame update

win = Tk()
win.geometry('1920x1080')
win.bind("<Configure>", enforce_aspect)

canvas = tk.Canvas(win, width=1920, height=1080)
canvas.pack(fill=tk.BOTH, expand=True)
update_frame()

win.mainloop()