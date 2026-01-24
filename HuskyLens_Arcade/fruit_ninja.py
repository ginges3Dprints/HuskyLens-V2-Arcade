import pygame
import serial
import serial.tools.list_ports
import pyautogui
import json
import sys

# --- CONFIGURATION ---
SMOOTHING = 0.5
SCREEN_W, SCREEN_H = pyautogui.size()
CAM_W, CAM_H = 320, 240

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

def run():
    pygame.init()
    screen = pygame.display.set_mode((400, 200)) # Small status window
    pygame.display.set_caption("Fruit Ninja Controller")
    font = pygame.font.SysFont("Arial", 30)
    clock = pygame.time.Clock()

    port = find_port()
    ser = None
    if port:
        ser = serial.Serial(port, 115200, timeout=0.05)
        ser.dtr = True
        ser.rts = True
    
    curr_x, curr_y = SCREEN_W // 2, SCREEN_H // 2
    status_text = "Searching for Hand..."

    running = True
    while running:
        # 1. Handle Window Events (Exit)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        # 2. Read Sensor
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    if "x" in data and "y" in data:
                        raw_x = int(data["x"])
                        raw_y = int(data["y"])
                        
                        # Map to screen
                        target_x = (1.0 - (raw_x / CAM_W)) * SCREEN_W
                        target_y = (raw_y / CAM_H) * SCREEN_H
                        
                        # Smooth
                        curr_x = (curr_x * SMOOTHING) + (target_x * (1 - SMOOTHING))
                        curr_y = (curr_y * SMOOTHING) + (target_y * (1 - SMOOTHING))
                        
                        pyautogui.moveTo(int(curr_x), int(curr_y))
                        status_text = "Tracking Hand..."
            except: pass

        # 3. Draw Status
        screen.fill((30, 30, 30))
        text_surf = font.render(status_text, True, (0, 255, 0))
        hint_surf = font.render("Press ESC to Exit", True, (150, 150, 150))
        screen.blit(text_surf, (20, 50))
        screen.blit(hint_surf, (20, 100))
        pygame.display.flip()
        clock.tick(60)

    if ser: ser.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run()