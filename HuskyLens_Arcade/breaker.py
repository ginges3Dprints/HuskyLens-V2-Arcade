import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import math

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

CAM_W = 320

# Colors
BG_COLOR = (10, 10, 20)
PADDLE_COLOR = (0, 255, 255) # Cyan
BALL_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
GRAY = (100, 100, 100)

# Brick Colors (Rows)
BRICK_COLORS = [
    (255, 50, 50),   # Red
    (255, 150, 50),  # Orange
    (255, 255, 50),  # Yellow
    (50, 255, 50),   # Green
    (50, 150, 255)   # Blue
]

def find_port():
    return "COM8" 

class Brick:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, 80, 30)
        self.color = color
        self.active = True

    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, self.color, self.rect)
            pygame.draw.rect(screen, BG_COLOR, self.rect, 2) # Outline

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 25)
        
        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass

        self.reset_level()
        self.hand_x = SCREEN_WIDTH // 2
        self.is_fist = False
        self.last_fist = False
        self.state = "READY" # READY, PLAYING, WON, GAMEOVER

    def reset_level(self):
        self.paddle_width = 120
        self.paddle_rect = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 50, self.paddle_width, 20)
        
        self.ball_rect = pygame.Rect(SCREEN_WIDTH//2 - 10, SCREEN_HEIGHT - 80, 20, 20)
        self.ball_vel = [0, 0]
        
        self.bricks = []
        # Create 5 rows of bricks
        for row in range(5):
            for col in range(9): # 9 columns
                bx = 35 + (col * 82)
                by = 50 + (row * 32)
                self.bricks.append(Brick(bx, by, BRICK_COLORS[row]))

        self.score = 0
        self.lives = 3

    def read_sensor(self):
        if not self.ser:
            self.hand_x = pygame.mouse.get_pos()[0]
            if pygame.mouse.get_pressed()[0]: self.is_fist = True
            else: self.is_fist = False
            return

        if self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    gesture = data.get("gesture", "none")
                    if "x" in data:
                        raw_x = int(data["x"])
                        # Map Camera X to Screen X
                        target_x = ((CAM_W - raw_x) / CAM_W) * SCREEN_WIDTH
                        # Smooth movement
                        self.hand_x += (target_x - self.hand_x) * 0.5
                    
                    self.is_fist = (gesture == "grab")
            except: pass

    def update(self):
        self.read_sensor()
        
        # --- PADDLE MOVEMENT ---
        # Paddle always follows hand, regardless of state
        self.paddle_rect.centerx = int(self.hand_x)
        # Keep paddle on screen
        if self.paddle_rect.left < 0: self.paddle_rect.left = 0
        if self.paddle_rect.right > SCREEN_WIDTH: self.paddle_rect.right = SCREEN_WIDTH

        # --- READY STATE (Calibration) ---
        if self.state == "READY":
            # Ball sticks to paddle
            self.ball_rect.centerx = self.paddle_rect.centerx
            self.ball_rect.bottom = self.paddle_rect.top - 5
            
            # Start game on FIST
            if self.is_fist and not self.last_fist:
                self.state = "PLAYING"
                # Launch ball upwards with random angle
                angle = random.choice([-4, -2, 2, 4])
                self.ball_vel = [angle, -6]

        # --- PLAYING STATE ---
        elif self.state == "PLAYING":
            # Move Ball
            self.ball_rect.x += self.ball_vel[0]
            self.ball_rect.y += self.ball_vel[1]
            
            # Wall Collisions
            if self.ball_rect.left <= 0 or self.ball_rect.right >= SCREEN_WIDTH:
                self.ball_vel[0] *= -1
            if self.ball_rect.top <= 0:
                self.ball_vel[1] *= -1
            
            # Paddle Collision
            if self.ball_rect.colliderect(self.paddle_rect) and self.ball_vel[1] > 0:
                self.ball_vel[1] *= -1
                # Add "English" (spin) based on where it hit the paddle
                offset = (self.ball_rect.centerx - self.paddle_rect.centerx) / (self.paddle_width / 2)
                self.ball_vel[0] = offset * 8 # Max horizontal speed

            # Brick Collision
            hit_index = self.ball_rect.collidelist([b.rect for b in self.bricks if b.active])
            if hit_index != -1:
                # Find the actual brick object from active bricks
                active_bricks = [b for b in self.bricks if b.active]
                brick = active_bricks[hit_index]
                
                brick.active = False
                self.ball_vel[1] *= -1
                self.score += 10
                
                # Check Win
                if all(not b.active for b in self.bricks):
                    self.state = "WON"

            # Death Logic
            if self.ball_rect.top > SCREEN_HEIGHT:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "GAMEOVER"
                else:
                    self.state = "READY" # Reset ball to paddle

        # --- GAMEOVER / WON STATE ---
        elif self.state in ["GAMEOVER", "WON"]:
            if self.is_fist and not self.last_fist:
                self.reset_level()
                self.state = "READY"

        self.last_fist = self.is_fist

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Draw Bricks
        for b in self.bricks: b.draw(self.screen)
        
        # Draw Paddle
        pygame.draw.rect(self.screen, PADDLE_COLOR, self.paddle_rect, border_radius=10)
        
        # Draw Ball
        pygame.draw.ellipse(self.screen, BALL_COLOR, self.ball_rect)

        # Draw UI
        score_t = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        lives_t = self.font.render(f"Lives: {self.lives}", True, TEXT_COLOR)
        self.screen.blit(score_t, (20, 550))
        self.screen.blit(lives_t, (SCREEN_WIDTH - 150, 550))

        # --- TEXT OVERLAYS ---
        if self.state == "READY":
            # Instructions Box
            box = pygame.Surface((400, 120))
            box.set_alpha(150)
            box.fill((0,0,0))
            self.screen.blit(box, (200, 300))
            
            t1 = self.font.render("READY?", True, (255, 255, 0))
            t2 = self.small_font.render("Move hand to check tracking.", True, TEXT_COLOR)
            t3 = self.small_font.render("Make a FIST to Launch!", True, (50, 255, 50))
            
            self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 310))
            self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 360))
            self.screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 390))

        elif self.state == "GAMEOVER":
            t = self.font.render("GAME OVER", True, (255, 50, 50))
            sub = self.small_font.render("Fist to Restart", True, TEXT_COLOR)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 300))
            self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 350))

        elif self.state == "WON":
            t = self.font.render("YOU WIN!", True, (50, 255, 50))
            sub = self.small_font.render("Fist to Restart", True, TEXT_COLOR)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 300))
            self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 350))

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
    Game().run()