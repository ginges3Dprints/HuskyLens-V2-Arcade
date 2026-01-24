import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import time

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

CAM_W = 320
CAM_H = 240 # Keep this fix!

# Colors
GRASS_GREEN = (34, 139, 34)
HOLE_BLACK = (20, 20, 20)
MOLE_BROWN = (139, 69, 19)
HAMMER_HEAD = (100, 100, 100)
HAMMER_HANDLE = (150, 75, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

def find_port():
    return "COM8" 

class Mole:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 50, y - 50, 100, 100)
        self.x = x
        self.y = y
        self.is_up = False
        self.timer = 0
        self.stay_time = 0

    def pop_up(self, duration):
        if not self.is_up:
            self.is_up = True
            self.stay_time = duration
            self.timer = pygame.time.get_ticks()

    def update(self):
        if self.is_up:
            if pygame.time.get_ticks() - self.timer > self.stay_time:
                self.is_up = False 

    def draw(self, screen):
        pygame.draw.ellipse(screen, HOLE_BLACK, (self.x - 60, self.y - 30, 120, 60))
        if self.is_up:
            pygame.draw.ellipse(screen, MOLE_BROWN, (self.x - 40, self.y - 80, 80, 100))
            pygame.draw.circle(screen, (0,0,0), (self.x - 15, self.y - 60), 5)
            pygame.draw.circle(screen, (0,0,0), (self.x + 15, self.y - 60), 5)
            pygame.draw.circle(screen, (255,100,100), (self.x, self.y - 50), 8)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Hammer (Slower Version)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)

        self.port = find_port()
        self.ser = None
        
        print(f"Connecting to {self.port}...")
        try:
            self.ser = serial.Serial(self.port, 115200, timeout=0.05)
            self.ser.dtr = True
            self.ser.rts = True
        except Exception as e:
            print(f"ERROR: {e}")

        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2
        self.is_fist = False
        self.last_fist_state = False 

        # Grid
        self.moles = []
        start_x, start_y = 200, 150
        gap_x, gap_y = 200, 150
        for row in range(3):
            for col in range(3):
                self.moles.append(Mole(start_x + col*gap_x, start_y + row*gap_y))

        self.score = 0
        self.game_over = False
        self.timer = 60 
        self.start_ticks = pygame.time.get_ticks()
        self.hits = [] 

    def read_sensor(self):
        if not self.ser: return

        if self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if line and line.startswith("{"):
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
        if self.game_over: return

        self.read_sensor()
        
        seconds_passed = (pygame.time.get_ticks() - self.start_ticks) / 1000
        self.time_left = max(0, int(self.timer - seconds_passed))
        if self.time_left == 0: self.game_over = True

        # SLOWER LOGIC HERE:
        if random.randint(0, 100) < 2: # Lower chance to spawn (2%)
            mole = random.choice(self.moles)
            # Stay up for 3000ms to 5000ms (3 to 5 seconds)
            mole.pop_up(random.randint(3000, 5000)) 

        if self.is_fist and not self.last_fist_state:
            hammer_rect = pygame.Rect(self.hand_x - 30, self.hand_y - 30, 60, 60)
            for mole in self.moles:
                if mole.is_up and hammer_rect.colliderect(mole.rect):
                    mole.is_up = False 
                    self.score += 10
                    self.hits.append({"x": mole.x, "y": mole.y, "life": 30, "text": "BONK!"})

        self.last_fist_state = self.is_fist

        for mole in self.moles: mole.update()
        for hit in self.hits: hit["life"] -= 1
        self.hits = [h for h in self.hits if h["life"] > 0]

    def draw(self):
        self.screen.fill(GRASS_GREEN)
        for mole in self.moles: mole.draw(self.screen)

        for hit in self.hits:
            txt = self.font.render(hit["text"], True, RED)
            self.screen.blit(txt, (hit["x"] - 20, hit["y"] - 100))

        # Hammer Drawing
        if self.is_fist:
            pygame.draw.rect(self.screen, HAMMER_HANDLE, (int(self.hand_x), int(self.hand_y) - 20, 80, 20))
            pygame.draw.rect(self.screen, HAMMER_HEAD, (int(self.hand_x) + 60, int(self.hand_y) - 40, 40, 60))
        else:
            pygame.draw.rect(self.screen, HAMMER_HANDLE, (int(self.hand_x) - 10, int(self.hand_y), 20, 80))
            pygame.draw.rect(self.screen, HAMMER_HEAD, (int(self.hand_x) - 30, int(self.hand_y), 60, 40))
        
        # Red Dot Target
        pygame.draw.circle(self.screen, RED, (int(self.hand_x), int(self.hand_y)), 5)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        time_text = self.font.render(f"Time: {self.time_left}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(time_text, (SCREEN_WIDTH - 180, 20))

        if self.game_over:
            over = self.font.render("GAME OVER", True, RED)
            final = self.font.render(f"Final Score: {self.score}", True, WHITE)
            restart = self.font.render("Press SPACE to Restart", True, WHITE)
            self.screen.blit(over, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(final, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 10))
            self.screen.blit(restart, (SCREEN_WIDTH//2 - 180, SCREEN_HEIGHT//2 + 70))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.ser: self.ser.close()
                    pygame.quit()
                    sys.exit()
                if self.game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.score = 0
                        self.game_over = False
                        self.start_ticks = pygame.time.get_ticks()
                        self.moles = [Mole(m.x, m.y) for m in self.moles]

            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()