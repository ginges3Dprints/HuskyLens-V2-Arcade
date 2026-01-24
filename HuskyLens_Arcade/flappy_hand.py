import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import os
import math

# --- CONFIGURATION ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Physics
GRAVITY = 0.6
FLAP_STRENGTH = -10
PIPE_SPEED = 4
PIPE_GAP = 170
PIPE_FREQUENCY = 1500 # Milliseconds

# Colors
SKY_BLUE = (135, 206, 235)
PIPE_GREEN = (34, 139, 34)
BIRD_YELLOW = (255, 215, 0)
BIRD_ORANGE = (255, 140, 0) 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_GREEN = (50, 255, 50)
GOLD = (255, 215, 0)
RED = (255, 50, 50)

def find_port():
    return "COM8" 

class Bird:
    def __init__(self):
        self.rect = pygame.Rect(100, SCREEN_HEIGHT // 2, 34, 34)
        self.vel = 0
        
    def flap(self):
        self.vel = FLAP_STRENGTH
        
    def move(self):
        self.vel += GRAVITY
        self.rect.y += int(self.vel)
        
    def reset(self):
        self.rect.y = SCREEN_HEIGHT // 2
        self.vel = 0

    def draw(self, screen):
        cx, cy = self.rect.centerx, self.rect.centery
        # Body
        pygame.draw.circle(screen, BIRD_YELLOW, (cx, cy), 17)
        pygame.draw.circle(screen, BLACK, (cx, cy), 17, 2)
        # Wing
        pygame.draw.ellipse(screen, WHITE, (cx - 12, cy - 5, 14, 10))
        pygame.draw.ellipse(screen, BLACK, (cx - 12, cy - 5, 14, 10), 2)
        # Eye
        pygame.draw.circle(screen, WHITE, (cx + 8, cy - 5), 5)
        pygame.draw.circle(screen, BLACK, (cx + 8, cy - 5), 5, 2)
        pygame.draw.circle(screen, BLACK, (cx + 10, cy - 5), 2)
        # Beak
        beak_points = [(cx + 15, cy - 2), (cx + 15, cy + 6), (cx + 24, cy + 2)]
        pygame.draw.polygon(screen, BIRD_ORANGE, beak_points)
        pygame.draw.polygon(screen, BLACK, beak_points, 2)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(100, 400)
        self.passed = False
        self.top_rect = pygame.Rect(self.x, 0, 60, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, 60, SCREEN_HEIGHT - (self.height + PIPE_GAP))

    def move(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, screen):
        # Top pipe
        pygame.draw.rect(screen, PIPE_GREEN, self.top_rect)
        pygame.draw.rect(screen, BLACK, self.top_rect, 2)
        pygame.draw.rect(screen, PIPE_GREEN, (self.x - 2, self.height - 20, 64, 20))
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.height - 20, 64, 20), 2)
        
        # Bottom pipe
        pygame.draw.rect(screen, PIPE_GREEN, self.bottom_rect)
        pygame.draw.rect(screen, BLACK, self.bottom_rect, 2)
        pygame.draw.rect(screen, PIPE_GREEN, (self.x - 2, self.bottom_rect.y, 64, 20))
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.bottom_rect.y, 64, 20), 2)

    def collide(self, bird_rect):
        return self.top_rect.colliderect(bird_rect) or self.bottom_rect.colliderect(bird_rect)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Hand V4 (Gesture Restart)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 50, bold=True)
        
        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass
            
        self.load_leaderboard()
        self.reset_game()
        self.last_fist_state = False

    def load_leaderboard(self):
        self.high_scores = []
        if os.path.exists("flappy_scores.json"):
            try:
                with open("flappy_scores.json", "r") as f:
                    data = json.load(f)
                    if data and isinstance(data, list):
                        self.high_scores = data
            except: self.high_scores = []
        self.high_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.high_scores = self.high_scores[:5]

    def save_score(self, name):
        self.high_scores.append({"name": name, "score": self.score})
        self.high_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.high_scores = self.high_scores[:5]
        with open("flappy_scores.json", "w") as f:
            json.dump(self.high_scores, f)

    def reset_game(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.last_pipe_time = pygame.time.get_ticks()
        self.state = "READY"
        self.input_name = ""

    def read_sensor(self):
        is_fist = False
        if not self.ser:
            if pygame.mouse.get_pressed()[0]: is_fist = True
        else:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode().strip()
                    if line.startswith("{"):
                        data = json.loads(line)
                        if data.get("gesture") == "grab":
                            is_fist = True
                except: pass
        
        # --- INPUT HANDLING ---
        if is_fist and not self.last_fist_state:
            if self.state == "READY":
                self.state = "PLAYING"
                self.bird.flap()
            elif self.state == "PLAYING":
                self.bird.flap()
            elif self.state == "GAME_OVER":
                # --- THIS IS THE NEW RESTART LOGIC ---
                self.reset_game()
            
        self.last_fist_state = is_fist

    def update(self):
        self.read_sensor()
        
        if self.state == "READY":
            # Hover
            self.bird.rect.y = SCREEN_HEIGHT//2 + int(math.sin(pygame.time.get_ticks() * 0.005) * 10)
            return

        if self.state == "PLAYING":
            self.bird.move()
            current_time = pygame.time.get_ticks()
            if current_time - self.last_pipe_time > PIPE_FREQUENCY:
                self.pipes.append(Pipe(SCREEN_WIDTH + 50))
                self.last_pipe_time = current_time

            for pipe in self.pipes:
                pipe.move()
                if not pipe.passed and pipe.x < self.bird.rect.x:
                    self.score += 1
                    pipe.passed = True
                if pipe.collide(self.bird.rect):
                    self.game_over()

            self.pipes = [p for p in self.pipes if p.x > -100]
            if self.bird.rect.top < 0 or self.bird.rect.bottom > SCREEN_HEIGHT:
                self.game_over()

    def game_over(self):
        lowest = 0
        if len(self.high_scores) > 0: lowest = self.high_scores[-1]["score"]
        
        if self.score > lowest or len(self.high_scores) < 5:
            self.state = "INPUT_NAME"
        else:
            self.state = "GAME_OVER"

    def draw(self):
        self.screen.fill(SKY_BLUE)
        for pipe in self.pipes: pipe.draw(self.screen)
        self.bird.draw(self.screen)
        
        # Ground
        pygame.draw.rect(self.screen, (222, 184, 135), (0, SCREEN_HEIGHT-20, SCREEN_WIDTH, 20))
        pygame.draw.line(self.screen, (100, 200, 100), (0, SCREEN_HEIGHT-20), (SCREEN_WIDTH, SCREEN_HEIGHT-20), 5)

        if self.state == "READY":
            box = pygame.Surface((320, 150))
            box.set_alpha(200)
            box.fill(BLACK)
            self.screen.blit(box, (40, 200))
            t1 = self.font.render("GET READY!", True, GOLD)
            t2 = self.font.render("Make a FIST", True, WHITE)
            t3 = self.font.render("to Flap & Start", True, WHITE)
            self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, 220))
            self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, 270))
            self.screen.blit(t3, (SCREEN_WIDTH//2 - t3.get_width()//2, 310))

        elif self.state == "PLAYING":
            score_t = self.score_font.render(str(self.score), True, WHITE)
            score_outline = self.score_font.render(str(self.score), True, BLACK)
            self.screen.blit(score_outline, (SCREEN_WIDTH//2 - 22, 52))
            self.screen.blit(score_t, (SCREEN_WIDTH//2 - 20, 50))

        elif self.state == "INPUT_NAME":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0,0))
            t = self.font.render("NEW HIGH SCORE!", True, GOLD)
            s = self.font.render(f"Score: {self.score}", True, WHITE)
            p = self.font.render("Type Name (Keyboard):", True, SKY_BLUE)
            n = self.score_font.render(self.input_name + "_", True, WHITE)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 150))
            self.screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 200))
            self.screen.blit(p, (SCREEN_WIDTH//2 - p.get_width()//2, 280))
            self.screen.blit(n, (SCREEN_WIDTH//2 - n.get_width()//2, 330))

        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(220)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0,0))
            t = self.score_font.render("GAME OVER", True, RED)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 50))
            
            t_lb = self.font.render("- BEST FLAPPERS -", True, GOLD)
            self.screen.blit(t_lb, (SCREEN_WIDTH//2 - t_lb.get_width()//2, 130))
            for i, entry in enumerate(self.high_scores):
                col = NEON_GREEN if entry["score"] == self.score and entry.get("name") == self.input_name else WHITE
                txt = self.font.render(f"{i+1}. {entry['name']} ... {entry['score']}", True, col)
                self.screen.blit(txt, (60, 180 + i*40))
                
            # --- NEW INSTRUCTION TEXT ---
            restart = self.font.render("Make a FIST to Retry", True, SKY_BLUE)
            self.screen.blit(restart, (SCREEN_WIDTH//2 - restart.get_width()//2, 500))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.ser: self.ser.close()
                    pygame.quit()
                    sys.exit()
                
                # Keyboard needed for typing name
                if self.state == "INPUT_NAME" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.input_name == "": self.input_name = "Player"
                        self.save_score(self.input_name)
                        self.state = "GAME_OVER"
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    else:
                        if len(self.input_name) < 8 and event.unicode.isalnum():
                            self.input_name += event.unicode.upper()
                            
                # Backup spacebar restart (optional)
                if self.state == "GAME_OVER" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()

            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()