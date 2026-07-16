import pygame
import serial
import serial.tools.list_ports
import json
import sys
import os
import subprocess

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

CAM_W = 320
CAM_H = 240

# Colors
BG_COLOR = (15, 15, 25)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
BUTTON_COLOR = (40, 40, 60)
BUTTON_HOVER = (60, 100, 150)
TEXT_COLOR = (200, 200, 200)

def find_port():
    return "COM12" 

# --- GAME LIST ---
GAMES = [
    {"name": "Space Dodge", "file": "space_game_v7.py"},
    {"name": "Flappy Hand", "file": "flappy_hand_v4.py"},
    {"name": "Husky Pop", "file": "bubble_pop_v2.py"},
    {"name": "Husky Tac Toe", "file": "tictactoe_v2.py"},
    {"name": "Husky Dance", "file": "husky_dance_v2.py"},
    {"name": "Husky Breaker", "file": "husky_breaker.py"},
    {"name": "Husky Hammer", "file": "hammer_game.py"},
    {"name": "Camera Test", "file": "test_tracking.py"}
]

class Launcher:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("HuskyLens Arcade Launcher")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.btn_font = pygame.font.SysFont("Arial", 30, bold=True)
        
        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass

        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2
        self.is_fist = False
        self.last_fist = False

        # Generate Button Rectangles
        self.buttons = []
        start_y = 120
        btn_h = 55
        spacing = 10
        for i, game in enumerate(GAMES):
            rect = pygame.Rect(150, start_y + i*(btn_h + spacing), 500, btn_h)
            self.buttons.append((rect, game))

    def read_sensor(self):
        if not self.ser:
            self.hand_x, self.hand_y = pygame.mouse.get_pos()
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

    def launch_game(self, file_name):
        # 1. Close the serial port so the game can use it
        if self.ser: 
            self.ser.close()
        
        # 2. Close Pygame window
        pygame.quit()
        
        print(f"Launching {file_name}...")
        
        # 3. Run the game script and wait for it to finish
        subprocess.run([sys.executable, file_name])
        
        # 4. Once the game is closed, restart the launcher automatically!
        os.execl(sys.executable, sys.executable, *sys.argv)

    def update(self):
        self.read_sensor()
        
        cursor = pygame.Rect(self.hand_x, self.hand_y, 1, 1)
        
        # Check clicks
        if self.is_fist and not self.last_fist:
            for rect, game in self.buttons:
                if cursor.colliderect(rect):
                    self.launch_game(game["file"])
                    return # Stop updating
                    
        self.last_fist = self.is_fist

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Title
        title = self.title_font.render("HUSKYLENS ARCADE", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Draw Buttons
        cursor = pygame.Rect(self.hand_x, self.hand_y, 1, 1)
        for rect, game in self.buttons:
            if cursor.colliderect(rect):
                pygame.draw.rect(self.screen, BUTTON_HOVER, rect, border_radius=10)
                pygame.draw.rect(self.screen, CYAN, rect, 3, border_radius=10) # Highlight outline
                txt = self.btn_font.render(game["name"], True, WHITE)
            else:
                pygame.draw.rect(self.screen, BUTTON_COLOR, rect, border_radius=10)
                txt = self.btn_font.render(game["name"], True, TEXT_COLOR)
                
            self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # Draw Hand Cursor
        if self.is_fist:
            pygame.draw.circle(self.screen, CYAN, (int(self.hand_x), int(self.hand_y)), 15)
        else:
            pygame.draw.circle(self.screen, WHITE, (int(self.hand_x), int(self.hand_y)), 10)
            pygame.draw.circle(self.screen, CYAN, (int(self.hand_x), int(self.hand_y)), 14, 2)

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
            self.clock.tick(FPS)

if __name__ == "__main__":
    Launcher().run()