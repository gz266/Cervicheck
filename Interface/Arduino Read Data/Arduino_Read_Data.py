import serial

arduinoData = serial.Serial('/dev/cu.usbmodem1101', baudrate=9600, timeout=1)  # Adjust the port as necessary

while True:
    data = input("Enter in number")
    data = data + '\r'
    arduinoData.write(data.encode())
    
