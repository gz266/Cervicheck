import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
import serial
from time import sleep
import pandas as pd
from tkinter import filedialog

#start serial
commPort = "COM6"
ser = serial.Serial(commPort, baudrate=9600, timeout=1)
sleep(2)


running = False
rows = []
df = pd.DataFrame()


root = tk.Tk()
root.title("Impedance Dashboard")


output = ScrolledText(root, height=10, width=60)
output.pack()

def update_output(text):
    output.insert(tk.END, text + "\n")
    output.see(tk.END)

#table frame
table_frame = tk.Frame(root)
table_frame.pack()

table = ttk.Treeview(
    root,
    columns=("RFB", "CAL", "TEST", "IMP"),
    show="headings"
)

table.heading("RFB", text="RFB")
table.heading("CAL", text="Calibration")
table.heading("TEST", text="Test")
table.heading("IMP", text="Impedance")

# Vertical scrollbar
scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar_y.set)

# Layout
table.grid(row=0, column=0, sticky="nsew")
scrollbar_y.grid(row=0, column=1, sticky="ns")


table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

table.pack()


def update_table():
    global df

    # clear table
    for item in table.get_children():
        table.delete(item)

    # show the last row of values in the table
    for _, row in df.tail(200).iterrows():
        table.insert(
            "",
            "end",
            values=(
                row["RFB"],
                row["CalibrationResistance"],
                row["TestResistance"],
                row["Impedance"]
            )
        )

#start the read serial
def read_serial():
    global running, rows, df

    while running:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            # ignore Arduino startup messages - don't know if we need this
            if "Calibrated" in line or "FAILED" in line or "Let's Rock" in line:
                continue

            #split the string
            parts = line.split(",")

            if len(parts) != 4:
                continue

            rfb, cal, test, imp = [p.strip() for p in parts]

            row = {
                "RFB": int(rfb),
                "CalibrationResistance": int(cal),
                "TestResistance": int(test),
                "Impedance": float(imp)
            }

            rows.append(row)
            df = pd.DataFrame(rows)

            root.after(0, update_table)

        except Exception as e:
            root.after(0, update_output, f"Error: {e}")



#start run
def start_run():
    global running

    if not running:
        running = True
        ser.write(b's')

        threading.Thread(target=read_serial, daemon=True).start()
        update_output("Started run")

start_button = tk.Button(root, text="Start run", command=start_run)
start_button.pack()

stop_button = tk.Button(root, text="Stop run", command = stop_run)
stop_button.pack()

save_button = tk.Button(root, text="Save to csv", command = save_csv)

#stop the run
def stop_run():
    global running

    if not running:
        running = False
        try:
            ser.write(b'x')
        except:
            pass
    update_output("Stopped run")


#save to csv
def save_csv():
   global df

   if df.empty:
       update_output("No data to save")
       return 
   file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save Data"
    )

    
   if not file_path:
        return 

   try:
        df.to_csv(file_path, index=False)
        update_output(f"Saved data to {file_path}")
   except Exception as e:
        update_output(f"Error saving file: {e}")




root.mainloop()