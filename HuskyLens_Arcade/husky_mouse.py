import serial
import serial.tools.list_ports
import pyautogui
import json
import time

# --- CONFIGURATION ---
# Smoothing helps stop the mouse from shaking
# 0.1 = Very fast/jittery, 0.9 = Very slow/smooth
SMOOTHING = 0.6 

# HuskyLens Resolution
CAM_W = 320
CAM_H = 240

# Get Computer Screen Size
SCREEN_W, SCREEN_H = pyautogui.size()

# Safety Fail-safe: Slam mouse to corner to stop script
pyautogui.FAILSAFE = True

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

class HuskyMouse:
    def __init__(self):
        self.port = find_port()
        if not self.port:
            print("❌ ESP32 NOT FOUND! Check connection.")
            exit()
            
        print(f"✅ Mouse Active on {self.port}")
        print("   - PALM to Move")
        print("   - FIST to Click/Drag")
        print("   - Slam mouse to corner to emergency stop.")

        self.ser = serial.Serial(self.port, 115200, timeout=0.05)
        # --- CRITICAL FIX FOR ESP32-C3 ---
        self.ser.dtr = True
        self.ser.rts = True
        
        # State variables
        self.curr_x = SCREEN_W // 2
        self.curr_y = SCREEN_H // 2
        self.is_dragging = False

    def map_coordinates(self, raw_x, raw_y):
        # 1. Mirror X axis (Camera sees opposite)
        x_mirrored = CAM_W - raw_x
        
        # 2. Map Camera Resolution to Screen Resolution
        target_x = (x_mirrored / CAM_W) * SCREEN_W
        target_y = (raw_y / CAM_H) * SCREEN_H
        
        # 3. Apply Smoothing (Linear Interpolation)
        self.curr_x = (self.curr_x * SMOOTHING) + (target_x * (1 - SMOOTHING))
        self.curr_y = (self.curr_y * SMOOTHING) + (target_y * (1 - SMOOTHING))
        
        return int(self.curr_x), int(self.curr_y)

    def run(self):
        try:
            while True:
                if self.ser.in_waiting:
                    try:
                        line = self.ser.readline().decode().strip()
                        if not line.startswith("{"): continue
                        
                        data = json.loads(line)
                        gesture = data.get("gesture", "none")
                        
                        # --- MOVEMENT (PALM) ---
                        if "x" in data and "y" in data:
                            raw_x = int(data["x"])
                            raw_y = int(data["y"])
                            
                            final_x, final_y = self.map_coordinates(raw_x, raw_y)
                            
                            # Move the mouse
                            # (duration=0 makes it instant)
                            pyautogui.moveTo(final_x, final_y, duration=0)

                        # --- CLICKING (FIST) ---
                        if gesture == "grab":
                            if not self.is_dragging:
                                pyautogui.mouseDown()
                                print("🔻 Click/Hold")
                                self.is_dragging = True
                        
                        # --- RELEASE ---
                        elif gesture == "hand_open" or gesture == "release":
                            if self.is_dragging:
                                pyautogui.mouseUp()
                                print("🔺 Release")
                                self.is_dragging = False
                                
                    except json.JSONDecodeError:
                        pass
                    except pyautogui.FailSafeException:
                        print("\n🛑 FAILSAFE TRIGGERED (Mouse in corner)")
                        break
                        
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.ser.close()

if __name__ == "__main__":
    HuskyMouse().run()