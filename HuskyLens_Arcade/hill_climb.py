import pygame
import serial
import serial.tools.list_ports
import pyautogui
import json
import sys

GAS_ZONE = 90
BRAKE_ZONE = 150

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

def run():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Hill Climb Controller")
    font = pygame.font.SysFont("Arial", 40, bold=True)
    clock = pygame.time.Clock()

    port = find_port()
    ser = None
    if port:
        ser = serial.Serial(port, 115200, timeout=0.05)
        ser.dtr = True
        ser.rts = True

    state = "NEUTRAL"

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
                    if data.get("gesture") == "hand_open" and "y" in data:
                        y = int(data["y"])

                        if y < GAS_ZONE:
                            if state != "GAS":
                                pyautogui.keyDown('right'); pyautogui.keyUp('left')
                                state = "GAS"
                        elif y > BRAKE_ZONE:
                            if state != "BRAKE":
                                pyautogui.keyDown('left'); pyautogui.keyUp('right')
                                state = "BRAKE"
                        else:
                            if state != "NEUTRAL":
                                pyautogui.keyUp('left'); pyautogui.keyUp('right')
                                state = "NEUTRAL"
            except: pass

        # Draw UI
        screen.fill((20, 20, 40))
        
        # Status Text
        color = (255, 255, 255)
        if state == "GAS": color = (0, 255, 0)
        elif state == "BRAKE": color = (255, 50, 50)
        
        text = font.render(state, True, color)
        text_rect = text.get_rect(center=(200, 150))
        screen.blit(text, text_rect)

        hint = pygame.font.SysFont("Arial", 20).render("Press ESC to Exit", True, (150, 150, 150))
        screen.blit(hint, (130, 250))

        pygame.display.flip()
        clock.tick(60)

    # Cleanup keys on exit so car doesn't keep driving
    pyautogui.keyUp('left')
    pyautogui.keyUp('right')
    if ser: ser.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run()