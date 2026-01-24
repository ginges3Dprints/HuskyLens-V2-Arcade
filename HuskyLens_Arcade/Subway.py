import pygame
import serial
import serial.tools.list_ports
import pyautogui
import json
import sys

# --- ZONES ---
UP_LIMIT = 80
DOWN_LIMIT = 160
LEFT_LIMIT = 100
RIGHT_LIMIT = 220

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

def run():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Subway Surfers Controller")
    font = pygame.font.SysFont("Arial", 40, bold=True)
    clock = pygame.time.Clock()

    port = find_port()
    ser = None
    if port:
        ser = serial.Serial(port, 115200, timeout=0.05)
        ser.dtr = True
        ser.rts = True

    last_action = "CENTER"
    current_action = "CENTER"

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    if data.get("gesture") == "hand_open" and "x" in data:
                        x = int(data["x"])
                        y = int(data["y"])
                        x_mirrored = 320 - x

                        new_action = "CENTER"
                        if y < UP_LIMIT: new_action = "JUMP"
                        elif y > DOWN_LIMIT: new_action = "ROLL"
                        elif x_mirrored < LEFT_LIMIT: new_action = "LEFT"
                        elif x_mirrored > RIGHT_LIMIT: new_action = "RIGHT"

                        if new_action != last_action:
                            if new_action == "JUMP": pyautogui.press('up')
                            elif new_action == "ROLL": pyautogui.press('down')
                            elif new_action == "LEFT": pyautogui.press('left')
                            elif new_action == "RIGHT": pyautogui.press('right')
                            last_action = new_action
                        
                        current_action = new_action
            except: pass

        # Draw UI
        screen.fill((20, 20, 40))
        
        # Action Text
        color = (255, 255, 255)
        if current_action != "CENTER": color = (0, 255, 0)
        
        text = font.render(current_action, True, color)
        text_rect = text.get_rect(center=(200, 150))
        screen.blit(text, text_rect)

        # Instructions
        hint = pygame.font.SysFont("Arial", 20).render("Press ESC to Exit", True, (150, 150, 150))
        screen.blit(hint, (130, 250))

        pygame.display.flip()
        clock.tick(60)

    if ser: ser.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run()