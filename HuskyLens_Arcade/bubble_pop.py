import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import math
import array

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

CAM_W = 320

# Colors
BG_COLOR = (135, 206, 250) 
BUBBLE_COLOR = (255, 255, 255)
POWER_BUBBLE_COLOR = (255, 50, 50) # RED
NEEDLE_COLOR = (100, 100, 100)
TEXT_COLOR = (0, 0, 100)

def find_port():
    return "COM8" 

# --- SOUND GENERATOR (No Files Needed!) ---
class SoundGen:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.pop_sound = self.make_sound(400, 0.1, "noise")
            self.power_sound = self.make_sound(800, 0.3, "square")
            self.nuke_sound = self.make_sound(150, 0.5, "noise")
        except:
            self.pop_sound = None

    def make_sound(self, freq, duration, type):
        # Generates raw audio data
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            if type == "noise":
                val = random.randint(-10000, 10000)
            elif type == "square":
                val = 10000 if int(i * freq / sample_rate) % 2 else -10000
            else:
                val = 0
            
            # Fade out
            decay = (n_samples - i) / n_samples
            buf[i] = int(val * decay)
            
        return pygame.mixer.Sound(buffer=buf)

    def play(self, name):
        if not pygame.mixer.get_init(): return
        if name == "pop" and self.pop_sound: self.pop_sound.play()
        if name == "power" and self.power_sound: self.power_sound.play()
        if name == "nuke" and self.nuke_sound: self.nuke_sound.play()

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = 30
        self.size = random.randint(3, 8)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            alpha = int((self.life / 30) * 255)
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
            screen.blit(s, (self.x - self.size, self.y - self.size))

class Bubble:
    def __init__(self):
        self.radius = random.randint(25, 55)
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = SCREEN_HEIGHT + self.radius
        self.speed = random.uniform(2, 4)
        self.timer = random.random() * 100
        
        # 1 in 15 chance to be a MYSTERY POWERUP
        self.is_powerup = (random.randint(0, 15) == 0)
        self.color = POWER_BUBBLE_COLOR if self.is_powerup else BUBBLE_COLOR
        
    def update(self, speed_mod):
        self.y -= self.speed * speed_mod
        self.x += math.sin(self.timer) * 1.5
        self.timer += 0.05

    def draw(self, screen):
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        
        # Color Body
        c = self.color
        pygame.draw.circle(s, (*c, 100), (self.radius, self.radius), self.radius)
        # Rim
        pygame.draw.circle(s, (255, 255, 255, 200), (self.radius, self.radius), self.radius, 3)
        # Shine
        pygame.draw.ellipse(s, (255, 255, 255, 230), (self.radius//3, self.radius//3, self.radius//2, self.radius//4))
        
        screen.blit(s, (self.x - self.radius, self.y - self.radius))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Pop V2 (Sound + Chaos)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.alert_font = pygame.font.SysFont("Arial", 60, bold=True)
        
        # Init Sound
        self.sound = SoundGen()

        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass
            
        self.reset_game()

    def reset_game(self):
        self.bubbles = []
        self.particles = []
        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2
        self.is_fist = False
        self.last_fist_state = False
        self.score = 0
        
        # Powerup States
        self.needle_radius = 10
        self.speed_mod = 1.0
        self.power_timer = 0
        self.alert_text = ""
        self.alert_timer = 0

    def trigger_chaos(self):
        effect = random.choice(["NUKE", "GIANT", "JACKPOT", "SLOW"])
        self.sound.play("power")
        
        if effect == "NUKE":
            self.alert_text = "NUKE!"
            self.sound.play("nuke")
            # Pop all bubbles
            for b in self.bubbles:
                self.score += 10
                for _ in range(5):
                    self.particles.append(Particle(b.x, b.y, b.color))
            self.bubbles = []

        elif effect == "GIANT":
            self.alert_text = "GIANT NEEDLE!"
            self.needle_radius = 100 # Huge radius
            self.power_timer = 300 # 5 seconds (60fps * 5)

        elif effect == "JACKPOT":
            self.alert_text = "JACKPOT +500!"
            self.score += 500

        elif effect == "SLOW":
            self.alert_text = "SLOW MO..."
            self.speed_mod = 0.2
            self.power_timer = 180 # 3 seconds

        self.alert_timer = 120 # Show text for 2 seconds

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
                        target_y = (raw_y / 240) * SCREEN_HEIGHT
                        self.hand_x += (target_x - self.hand_x) * 0.5
                        self.hand_y += (target_y - self.hand_y) * 0.5
                    
                    self.is_fist = (gesture == "grab")
            except: pass

    def update(self):
        self.read_sensor()

        # Handle Timers
        if self.power_timer > 0:
            self.power_timer -= 1
        else:
            # Reset effects
            self.needle_radius = 10
            self.speed_mod = 1.0

        if self.alert_timer > 0: self.alert_timer -= 1

        # Spawn Bubbles
        if random.randint(0, 60) < 2: 
            self.bubbles.append(Bubble())

        # Update Bubbles
        for b in self.bubbles: b.update(self.speed_mod)
        self.bubbles = [b for b in self.bubbles if b.y > -50]

        # POP LOGIC
        if self.is_fist: 
            for b in self.bubbles[:]:
                # Distance Check
                hit_x = self.hand_x
                hit_y = self.hand_y - 20
                dist = math.hypot(b.x - hit_x, b.y - hit_y)
                
                # Check collision with Needle Radius (might be Giant)
                if dist < b.radius + self.needle_radius:
                    self.bubbles.remove(b)
                    
                    # Particles
                    for _ in range(8):
                        self.particles.append(Particle(b.x, b.y, b.color))
                    
                    if b.is_powerup:
                        self.trigger_chaos()
                    else:
                        self.sound.play("pop")
                        self.score += 10

        # Update Particles
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        for b in self.bubbles: b.draw(self.screen)
        for p in self.particles: p.draw(self.screen)

        # Draw Needle
        if self.is_fist:
            color = (255, 0, 0) if self.needle_radius > 10 else (50, 50, 50)
            
            # If Giant mode, draw a big circle
            if self.needle_radius > 10:
                s = pygame.Surface((200, 200), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 50), (100, 100), self.needle_radius)
                self.screen.blit(s, (self.hand_x - 100, self.hand_y - 120))
            
            # Sharp Needle
            pygame.draw.line(self.screen, color, (self.hand_x, self.hand_y + 40), (self.hand_x, self.hand_y - 20), 4)
            pygame.draw.circle(self.screen, (200, 50, 50), (self.hand_x, self.hand_y + 40), 10)
            pygame.draw.circle(self.screen, (255, 255, 255), (self.hand_x, self.hand_y - 20), 2)
        else:
            pygame.draw.circle(self.screen, (255, 255, 255), (int(self.hand_x), int(self.hand_y)), 10)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(self.hand_x), int(self.hand_y)), 10, 2)

        # UI
        score_t = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_t, (20, 20))

        # Alert Text
        if self.alert_timer > 0:
            alert = self.alert_font.render(self.alert_text, True, (255, 0, 0))
            # Shake effect
            off_x = random.randint(-5, 5)
            off_y = random.randint(-5, 5)
            self.screen.blit(alert, (SCREEN_WIDTH//2 - alert.get_width()//2 + off_x, SCREEN_HEIGHT//2 + off_y))

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