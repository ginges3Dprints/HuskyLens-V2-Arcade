import serial
import serial.tools.list_ports
import time

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Look for ESP32-C3 specific names
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

port = find_port()
if not port:
    print("❌ ESP32 NOT FOUND!")
else:
    print(f"✅ Connected to {port}")
    try:
        # Open connection
        ser = serial.Serial(port, 115200, timeout=0.1)
        
        # --- THE FIX: WAKE UP THE C3 CHIP ---
        ser.dtr = True
        ser.rts = True
        time.sleep(1) # Give it a second to wake up
        # ------------------------------------

        print("Waiting for data... (Show your hand!)")
        
        while True:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        print(f"Data: {line}")
                except:
                    pass
    except Exception as e:
        print(f"Error: {e}")