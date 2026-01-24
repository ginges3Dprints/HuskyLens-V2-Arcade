import pygame
import serial
import serial.tools.list_ports
import json
import pyautogui
import sys
import warnings

# --- HIDE WARNINGS ---
# This hides the "pkg_resources" warning you saw
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
BUTTON_COLOR = (50, 50, 60)
HOVER_COLOR = (100, 100, 120)
ACTIVE_COLOR = (0, 255, 0)
TEXT_COLOR = (255, 255, 255)
BAR_COLOR = (30, 30, 30)
FILL_COLOR = (0, 200, 255)

# Camera Mapping
CAM_W = 320
CAM_H = 240

def find_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(x in p.description.lower() for x in ["cp210", "ch340", "espressif", "usb-serial", "device"]):
            return p.device
    return None

class Button:
    def __init__(self, x, y, w, h, text, action_key):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action_key = action_key
        self.is_hovered = False
        self.cooldown = 0

    def draw(self, screen):
        color = BUTTON_COLOR
        if self.is_hovered: color = HOVER_COLOR
        if self.cooldown > 0: color = ACTIVE_COLOR
        
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        pygame.draw.rect(screen, (200,200,200), self.rect, 2, border_radius=15)
        
        font = pygame.font.SysFont("Arial", 40, bold=True)
        txt_surf = font.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def update(self, is_fist):
        if self.cooldown > 0:
            self.cooldown -= 1
            return

        if self.is_hovered and is_fist:
            try:
                print(f"Action: {self.text}")
                pyautogui.press(self.action_key)
            except Exception as e:
                print(f"Error pressing key: {e}")
            self.cooldown = 30 

class VolumeSlider:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.level = 0.5 
        self.is_dragging = False

    def update(self, hand_x, is_fist):
        if self.rect.collidepoint(hand_x, self.rect.centery):
            if is_fist:
                self.is_dragging = True
        
        if not is_fist:
            self.is_dragging = False

        if self.is_dragging:
            relative_x = hand_x - self.rect.x
            self.level = max(0, min(1, relative_x / self.rect.width))
            
            try:
                if self.level > 0.5: pyautogui.press('volumeup')
                elif self.level < 0.5: pyautogui.press('volumedown')
            except: pass

    def draw(self, screen):
        pygame.draw.rect(screen, BAR_COLOR, self.rect, border_radius=10)
        fill_w = int(self.rect.width * self.level)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
        pygame.draw.rect(screen, FILL_COLOR, fill_rect, border_radius=10)
        knob_x = self.rect.x + fill_w
        pygame.draw.circle(screen, (255,255,255), (knob_x, self.rect.centery), 20)
        
        font = pygame.font.SysFont("Arial", 30)
        text = font.render("VOLUME (Grab & Drag)", True, (255,255,255))
        screen.blit(text, (self.rect.x, self.rect.y - 40))

class Remote:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Media Remote")
        self.clock = pygame.time.Clock()

        port = find_port()
        self.ser = None
        if port:
            try:
                self.ser = serial.Serial(port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
                print(f"Connected to {port}")
            except Exception as e:
                print(f"Serial Error: {e}")

        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2
        self.is_fist = False

        self.buttons = [
            Button(325, 150, 150, 100, "PLAY/||", "playpause"),
            Button(100, 150, 150, 100, "<< PREV", "prevtrack"),
            Button(550, 150, 150, 100, "NEXT >>", "nexttrack")
        ]
        self.volume = VolumeSlider(100, 350, 600, 40)

    def read_sensor(self):
        if not self.ser:
            mx, my = pygame.mouse.get_pos()
            self.hand_x, self.hand_y = mx, my
            self.is_fist = pygame.mouse.get_pressed()[0]
            return

        if self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    gesture = data.get("gesture", "none")

                    if "x" in data:
                        raw_x = int(data["x"])
                        raw_y = int(data["y"])
                        target_x = ((CAM_W - raw_x) / CAM_W) * SCREEN_WIDTH
                        target_y = (raw_y / CAM_H) * SCREEN_HEIGHT
                        self.hand_x += (target_x - self.hand_x) * 0.5
                        self.hand_y += (target_y - self.hand_y) * 0.5

                    self.is_fist = (gesture == "grab")
            except: pass

    def update(self):
        self.read_sensor()
        for btn in self.buttons:
            btn.is_hovered = btn.rect.collidepoint(self.hand_x, self.hand_y)
            btn.update(self.is_fist)
        self.volume.update(self.hand_x, self.is_fist)

    def draw(self):
        self.screen.fill((20, 20, 30))
        for btn in self.buttons: btn.draw(self.screen)
        self.volume.draw(self.screen)
        
        cursor_color = ACTIVE_COLOR if self.is_fist else (255, 255, 255)
        pygame.draw.circle(self.screen, cursor_color, (int(self.hand_x), int(self.hand_y)), 15)
        pygame.draw.circle(self.screen, (0,0,0), (int(self.hand_x), int(self.hand_y)), 15, 2)

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.ser: self.ser.close()
                    pygame.quit()
                    sys.exit()
            
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        Remote().run()
    except Exception as e:
        # IF IT CRASHES, IT WILL PRINT THE ERROR HERE
        print(f"CRITICAL ERROR: {e}")
        input("Press Enter to close...")