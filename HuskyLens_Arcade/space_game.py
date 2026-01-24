import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import os
import traceback 

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (10, 10, 20)
WHITE = (255, 255, 255)
NEON_BLUE = (0, 255, 255)
NEON_RED = (255, 50, 50)
NEON_GREEN = (50, 255, 50)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)

CAM_W = 320

def find_port():
    return "COM8" 

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.randint(2, 8)
        self.size = random.randint(1, 3)
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.size)

class Laser:
    def __init__(self, x, y):
        self.rect = pygame.Rect(int(x) - 2, int(y), 4, 20)
        self.color = NEON_GREEN
    def update(self):
        self.rect.y -= 10
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 20
        self.color = color
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)

class PowerUp:
    def __init__(self):
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = -50
        self.type = random.choice(["WEAPON", "HEALTH"])
        self.rect = pygame.Rect(self.x, self.y, 30, 30)
    
    def update(self):
        self.rect.y += 3
        
    def draw(self, screen):
        color = NEON_BLUE if self.type == "WEAPON" else NEON_GREEN
        pygame.draw.circle(screen, color, self.rect.center, 15)
        font = pygame.font.SysFont("Arial", 20, bold=True)
        txt = "W" if self.type == "WEAPON" else "+"
        surf = font.render(txt, True, BLACK)
        screen.blit(surf, (self.rect.x + 8, self.rect.y + 4))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Dodge V7 (Survival Score)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.input_font = pygame.font.SysFont("Arial", 60, bold=True)

        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass
        
        self.stars = [Star() for _ in range(50)]
        self.load_leaderboard()
        self.reset_game()
        
        self.state = "PLAYING" 
        self.input_name = ""

    def load_leaderboard(self):
        self.high_scores = []
        if os.path.exists("scores.json"):
            try:
                with open("scores.json", "r") as f:
                    data = json.load(f)
                    if data and isinstance(data, list):
                        if len(data) == 0: self.high_scores = []
                        elif isinstance(data[0], int) or isinstance(data[0], float):
                            self.high_scores = []
                        else:
                            self.high_scores = data
                    else:
                        self.high_scores = []
            except Exception as e:
                self.high_scores = []

        self.high_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.high_scores = self.high_scores[:5]

    def save_score(self, name):
        new_entry = {"name": name, "score": int(self.score)}
        self.high_scores.append(new_entry)
        self.high_scores.sort(key=lambda x: x["score"], reverse=True)
        self.high_scores = self.high_scores[:5]
        
        with open("scores.json", "w") as f:
            json.dump(self.high_scores, f)

    def reset_game(self):
        self.player_x = SCREEN_WIDTH // 2
        self.enemies = []
        self.lasers = []
        self.particles = []
        self.powerups = []
        self.score = 0
        self.health = 100
        self.weapon_level = 1
        self.speed_multiplier = 1.0
        self.last_shot_time = 0
        self.state = "PLAYING"
        self.input_name = ""

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > 250:
            y = SCREEN_HEIGHT - 100
            px = int(self.player_x)
            
            if self.weapon_level == 1:
                self.lasers.append(Laser(px, y))
            elif self.weapon_level == 2:
                self.lasers.append(Laser(px - 10, y))
                self.lasers.append(Laser(px + 10, y))
            else: 
                self.lasers.append(Laser(px, y - 5))
                self.lasers.append(Laser(px - 15, y))
                self.lasers.append(Laser(px + 15, y))
                
            self.last_shot_time = current_time

    def read_sensor(self):
        if not self.ser:
            mx, _ = pygame.mouse.get_pos()
            self.player_x = mx
            if pygame.mouse.get_pressed()[0]: self.shoot()
            return

        if self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                if line.startswith("{"):
                    data = json.loads(line)
                    gesture = data.get("gesture", "none")
                    if "x" in data:
                        raw_x = int(data["x"])
                        self.player_x = ((CAM_W - raw_x) / CAM_W) * SCREEN_WIDTH
                    if gesture == "grab":
                        self.shoot()
            except: pass

    def update(self):
        for s in self.stars: s.update()
        for p in self.particles: p.update()
        
        if self.state != "PLAYING": return

        self.read_sensor()
        
        # Survival Points
        self.score += 1

        if random.randint(0, 60) < 2 * self.speed_multiplier:
            size = random.randint(30, 60)
            enemy = pygame.Rect(random.randint(0, SCREEN_WIDTH-size), -size, size, size)
            self.enemies.append(enemy)

        if random.randint(0, 1000) < 5:
            self.powerups.append(PowerUp())

        for enemy in self.enemies: enemy.y += 4 * self.speed_multiplier
        for laser in self.lasers: laser.update()
        for p in self.powerups: p.update()

        self.enemies = [e for e in self.enemies if e.y < SCREEN_HEIGHT]
        self.lasers = [l for l in self.lasers if l.rect.y > 0]
        self.particles = [p for p in self.particles if p.life > 0]

        player_rect = pygame.Rect(int(self.player_x) - 20, SCREEN_HEIGHT - 80, 40, 40)

        # Collision: Laser vs Enemy
        for laser in self.lasers[:]:
            for enemy in self.enemies[:]:
                if laser.rect.colliderect(enemy):
                    self.lasers.remove(laser)
                    self.enemies.remove(enemy)
                    self.score += 100 
                    for _ in range(10): 
                        self.particles.append(Particle(enemy.centerx, enemy.centery, GRAY))
                    break

        # Collision: Player vs Enemy
        for enemy in self.enemies[:]:
            if player_rect.colliderect(enemy):
                self.enemies.remove(enemy)
                self.health -= 34
                self.particles.append(Particle(self.player_x, SCREEN_HEIGHT-80, NEON_RED))
                self.speed_multiplier = 1.0 
                if self.weapon_level > 1: self.weapon_level -= 1

        # Collision: Powerups
        for p in self.powerups[:]:
            if player_rect.colliderect(p.rect):
                if p.type == "WEAPON":
                    self.weapon_level = min(3, self.weapon_level + 1)
                    self.score += 200 
                elif p.type == "HEALTH":
                    self.health = min(100, self.health + 34)
                self.powerups.remove(p)

        if self.health <= 0:
            lowest_high_score = 0
            if len(self.high_scores) > 0:
                lowest_high_score = self.high_scores[-1]["score"]
            
            if self.score > lowest_high_score or len(self.high_scores) < 5:
                self.state = "INPUT_NAME"
            else:
                self.state = "GAME_OVER"

        self.speed_multiplier = 1.0 + (self.score / 5000.0)

    def draw(self):
        self.screen.fill(BLACK)
        for s in self.stars: s.draw(self.screen)
        
        if self.state == "PLAYING":
            px = int(self.player_x)
            pts = [(px, SCREEN_HEIGHT-90), (px-20, SCREEN_HEIGHT-50), (px+20, SCREEN_HEIGHT-50)]
            pygame.draw.polygon(self.screen, NEON_BLUE, pts)
            pygame.draw.polygon(self.screen, ORANGE, [(px-10, SCREEN_HEIGHT-50), (px+10, SCREEN_HEIGHT-50), (px, SCREEN_HEIGHT-30)])

            for l in self.lasers: l.draw(self.screen)
            for e in self.enemies:
                pygame.draw.circle(self.screen, GRAY, e.center, e.width//2)
                pygame.draw.circle(self.screen, (50,50,50), (e.centerx-5, e.centery-5), 5)
            for p in self.powerups: p.draw(self.screen)
            for p in self.particles: p.draw(self.screen)

            score_t = self.font.render(f"Score: {int(self.score)}", True, WHITE)
            self.screen.blit(score_t, (10, 10))
            pygame.draw.rect(self.screen, NEON_RED, (SCREEN_WIDTH-220, 10, 200, 20))
            if self.health > 0:
                pygame.draw.rect(self.screen, NEON_GREEN, (SCREEN_WIDTH-220, 10, self.health*2, 20))
            pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH-220, 10, 200, 20), 2)

        elif self.state == "INPUT_NAME":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0,0,50))
            self.screen.blit(overlay, (0,0))
            
            title = self.score_font.render("NEW HIGH SCORE!", True, GOLD)
            score_txt = self.font.render(f"Score: {int(self.score)}", True, WHITE)
            prompt = self.font.render("Type Your Name & Press Enter:", True, NEON_BLUE)
            name_txt = self.input_font.render(self.input_name + "_", True, WHITE)
            
            self.screen.blit(title, (SCREEN_WIDTH//2 - 200, 150))
            self.screen.blit(score_txt, (SCREEN_WIDTH//2 - 80, 220))
            self.screen.blit(prompt, (SCREEN_WIDTH//2 - 200, 300))
            self.screen.blit(name_txt, (SCREEN_WIDTH//2 - 100, 380))

        elif self.state == "GAME_OVER":
            over = self.score_font.render("GAME OVER", True, NEON_RED)
            self.screen.blit(over, (SCREEN_WIDTH//2 - 140, 50))
            
            lb_title = self.font.render("LEADERBOARD", True, GOLD)
            self.screen.blit(lb_title, (SCREEN_WIDTH//2 - 100, 150))
            
            for i, entry in enumerate(self.high_scores):
                color = WHITE
                if entry["score"] == int(self.score) and entry.get("name") == self.input_name: 
                    color = NEON_GREEN 
                
                name_str = entry.get("name", "Unknown")
                score_str = str(entry.get("score", 0))
                
                txt_name = self.font.render(f"{i+1}. {name_str}", True, color)
                txt_score = self.font.render(score_str, True, color)
                
                self.screen.blit(txt_name, (200, 220 + i*50))
                self.screen.blit(txt_score, (500, 220 + i*50))

            restart = self.font.render("Press SPACE to Restart", True, GRAY)
            self.screen.blit(restart, (SCREEN_WIDTH//2 - 140, 550))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.ser: self.ser.close()
                    pygame.quit()
                    sys.exit()
                
                if self.state == "INPUT_NAME" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.input_name == "": self.input_name = "Player"
                        self.save_score(self.input_name)
                        self.state = "GAME_OVER"
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    else:
                        if len(self.input_name) < 10 and event.unicode.isalnum():
                            self.input_name += event.unicode.upper()

                if self.state == "GAME_OVER" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()

            self.update()
            self.draw()
            self.clock.tick(FPS)

# --- CRASH CATCHER ---
if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("\n" + "="*40)
        print("CRITICAL ERROR CRASHED THE GAME")
        print("="*40)
        traceback.print_exc()
        print("="*40)
        input("Press Enter to close this window...")