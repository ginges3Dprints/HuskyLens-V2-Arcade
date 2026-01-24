# main_esp32.py
# -*- coding: utf-8 -*-
import json
import math
import threading
import time
import pygame
import serial
import serial.tools.list_ports
from angry_birds_game import AngryBirdsGame

# Configuration
FRAME_W = 320
FRAME_H = 240
BAUDRATE = 115200
COM_PORT = None  # Leave None to auto-detect
SMOOTH_ALPHA = 0.35
LAUNCH_GUARD_MS = 300

# --- HELPER FUNCTIONS ---

def auto_find_port():
    """
    Auto-detects ESP32 or Arduino ports.
    Updated to include keywords for ESP32-C3 / CP210x / CH340
    """
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = f"{p.description} {p.hwid}".lower()
        # Added 'espressif', 'cp210', 'slab' for ESP32 compatibility
        if any(k in desc for k in ["arduino", "wchusb", "ch340", "usb-serial", "espressif", "cp210", "slab"]):
            return p.device
    # Fallback: return the last port found if no keyword matches
    return ports[-1].device if ports else None


class SerialReader(threading.Thread):
    def __init__(self, port, baudrate):
        super().__init__(daemon=True)
        self.port_name = port
        self.baudrate = baudrate
        self.ser = None
        self.running = True
        self.latest = {}

    def run(self):
        while self.running:
            try:
                if not self.ser or not self.ser.is_open:
                    self._open()
                
                # Read line, decode, and strip whitespace
                line = self.ser.readline().decode(errors="ignore").strip()
                
                if not line:
                    continue
                
                # Parse JSON if valid
                if line.startswith("{") and line.endswith("}"):
                    try:
                        self.latest = json.loads(line)
                    except json.JSONDecodeError:
                        pass # Skip malformed lines
                        
            except Exception:
                # If connection is lost, close and retry
                try:
                    if self.ser:
                        self.ser.close()
                except Exception:
                    pass
                time.sleep(0.5)

    def _open(self):
        if not self.port_name:
            self.port_name = auto_find_port()
            if not self.port_name:
                raise RuntimeError("No available serial port found")
        
        # Open Serial Port
        self.ser = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
        
        # ESP32-C3 Native USB often needs DTR/RTS set to True to start stream
        self.ser.dtr = True
        self.ser.rts = True
        
        print(f"🔌 Serial connected: {self.port_name} @ {self.baudrate}")

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()


class EspHuskyController:
    def __init__(self):
        self.game = AngryBirdsGame()
        port = COM_PORT or auto_find_port()
        if not port:
            raise RuntimeError("No available serial port was found. Please set your COM_PORT manually.")
        
        self.reader = SerialReader(port, BAUDRATE)
        self.reader.start()

        self.grabbing = False
        self.aiming = False
        
        # Smoothing variables
        self._p_smooth = 0.0
        self._a_smooth = 0.0
        self._inited = False
        
        # Launch logic
        self._last_aim_power = 0.0
        self._last_aim_angle = 0.0
        self._last_launch_ts = 0.0

    def _smooth(self, p, a):
        if not self._inited:
            self._p_smooth, self._a_smooth = p, a
            self._inited = True
        else:
            self._p_smooth = (1 - SMOOTH_ALPHA) * self._p_smooth + SMOOTH_ALPHA * p
            self._a_smooth = (1 - SMOOTH_ALPHA) * self._a_smooth + SMOOTH_ALPHA * a
        return self._p_smooth, self._a_smooth

    def _handle_serial(self, data):
        """
        Interprets the JSON data from ESP32.
        Now prefers using 'power' and 'angle' directly from the ESP32.
        """
        gesture = str(data.get("gesture", "none"))
        
        # Retrieve values calculated by ESP32
        # Default to 0 if not present
        esp_power = float(data.get("power", 0.0))
        esp_angle = float(data.get("angle", 0.0))

        # --- FIST (Aiming) ---
        if gesture == "grab":
            self.grabbing = True
            self.aiming = True
            
            # Use the ESP32's calculated physics directly
            raw_power = esp_power
            raw_angle = esp_angle

            # Apply smoothing
            power, angle = self._smooth(raw_power, raw_angle)
            
            # Update state
            self._last_aim_power = power
            self._last_aim_angle = angle
            
            return {
                "power": power, 
                "angle": angle, 
                "should_launch": False
            }

        # --- OPEN HAND (Release) ---
        elif gesture == "release":
            # Logic: If we were aiming and the release happened recently
            # Check guards to prevent accidental double-fires
            should = (
                self.aiming
                and (time.time() * 1000 - self._last_launch_ts) > LAUNCH_GUARD_MS
            )
            
            # If release packet contains final power data, use it
            if should:
                final_power = esp_power if esp_power > 0 else self._last_aim_power
                final_angle = esp_angle if esp_angle != 0 else self._last_aim_angle
                
                params = {
                    "power": float(final_power),
                    "angle": float(final_angle),
                    "should_launch": True,
                }
                self._last_launch_ts = time.time() * 1000
                
                # Reset Flags
                self.grabbing = False
                self.aiming = False
                return params
            
            self.grabbing = False
            self.aiming = False
            return {"power": 0, "angle": 0, "should_launch": False}

        # --- IDLE / OPEN ---
        elif gesture == "hand_open":
            self.grabbing = False
            self.aiming = False
            return {"power": 0, "angle": 0, "should_launch": False}

        # Default fallback (keep aiming if we miss a packet but state is grabbing)
        if self.aiming:
             return {
                 "power": self._last_aim_power, 
                 "angle": self._last_aim_angle, 
                 "should_launch": False
             }
        
        return {"power": 0, "angle": 0, "should_launch": False}

    def run(self):
        print("🎮 ESP32-C3 + HUSKYLENS mode started")
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # 1. Get latest JSON from Serial Thread
            data = self.reader.latest or {}
            
            # 2. Process logic
            params = self._handle_serial(data)
            
            # 3. Update Game
            self.game.handle_gesture_input(params)
            self.game.update()
            self.game.draw()

            pygame.display.flip()
            clock.tick(60)

        self.reader.stop()
        pygame.quit()


if __name__ == "__main__":
    try:
        EspHuskyController().run()
    except Exception as e:
        print("Runtime error:", e)