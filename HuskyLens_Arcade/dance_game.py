import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import array

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

CAM_W = 320

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 0)

COLORS = [RED, GREEN, BLUE, YELLOW]

def find_port():
    return "COM8" 

# --- SOUND GENERATOR ---
class SoundGen:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.hit_sound = self.make_sound(600, 0.1, "square")
            self.miss_sound = self.make_sound(150, 0.3, "saw")
        except:
            self.hit_sound = None
            self.miss_sound = None

    def make_sound(self, freq, duration, type):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            if type == "square": val = 10000 if int(i * freq / sample_rate) % 2 else -10000
            else: val = random.randint(-5000, 5000)
            decay = (n_samples - i) / n_samples
            buf[i] = int(val * decay)
        return pygame.mixer.Sound(buffer=buf)

    def play(self, type):
        if not pygame.mixer.get_init(): return
        if type == "hit" and self.hit_sound: self.hit_sound.play()
        if type == "miss" and self.miss_sound: self.miss_sound.play()

class Note:
    def __init__(self, lane, speed):
        self.lane = lane # 0, 1, 2, 3
        self.x = 100 + (lane * 200) # Spacing
        self.y = -50
        self.speed = speed
        self.color = COLORS[lane]
        self.active = True
        
    def update(self):
        self.y += self.speed

    def draw(self, screen):
        # Draw Arrow Shape
        pygame.draw.circle(screen, self.color, (self.x, int(self.y)), 30)
        pygame.draw.circle(screen, WHITE, (self.x, int(self.y)), 30, 3)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Dance Revolution V2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 60, bold=True)
        
        self.sound = SoundGen()
        
        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass

        # Default Settings
        self.note_speed = 5
        self.spawn_rate = 60
        self.hit_y = 500

        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2 # Added Y for menu selection
        self.is_fist = False
        self.last_fist_state = False
        
        self.state = "MENU" # Start in menu
        self.score = 0
        self.combo = 0
        self.notes = []

    def start_game(self, difficulty):
        if difficulty == "SLOW":
            self.note_speed = 3
            self.spawn_rate = 80
        elif difficulty == "MEDIUM":
            self.note_speed = 6
            self.spawn_rate = 50
        elif difficulty == "FAST":
            self.note_speed = 9
            self.spawn_rate = 30
            
        self.notes = []
        self.score = 0
        self.combo = 0
        self.active_lane = 1
        self.feedback = ""
        self.feedback_timer = 0
        self.timer = 0
        self.state = "PLAYING"

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

    def check_hit(self):
        best_note = None
        min_dist = 1000
        
        for note in self.notes:
            if note.lane == self.active_lane and note.active:
                dist = abs(note.y - self.hit_y)
                if dist < min_dist:
                    min_dist = dist
                    best_note = note
        
        if best_note and min_dist < 60:
            best_note.active = False
            self.score += 100
            self.combo += 1
            self.sound.play("hit")
            
            if min_dist < 15: self.feedback = "PERFECT!"
            elif min_dist < 30: self.feedback = "GREAT!"
            else: self.feedback = "GOOD"
        else:
            self.combo = 0
            self.feedback = "MISS"
            self.sound.play("miss")
            
        self.feedback_timer = 30

    def update(self):
        self.read_sensor()
        
        # --- MENU LOGIC ---
        if self.state == "MENU":
            # Define Buttons
            btn_slow = pygame.Rect(200, 200, 400, 80)
            btn_med  = pygame.Rect(200, 300, 400, 80)
            btn_fast = pygame.Rect(200, 400, 400, 80)
            
            cursor = pygame.Rect(self.hand_x, self.hand_y, 1, 1)
            
            if self.is_fist and not self.last_fist_state:
                if cursor.colliderect(btn_slow): self.start_game("SLOW")
                elif cursor.colliderect(btn_med): self.start_game("MEDIUM")
                elif cursor.colliderect(btn_fast): self.start_game("FAST")
            
            self.last_fist_state = self.is_fist
            return

        # --- GAMEPLAY LOGIC ---
        
        # Calculate active lane (0-3) based on Hand X
        self.active_lane = int(self.hand_x // (SCREEN_WIDTH / 4))
        self.active_lane = max(0, min(3, self.active_lane))
        
        # Spawn Notes
        self.timer += 1
        if self.timer > self.spawn_rate:
            lane = random.randint(0, 3)
            self.notes.append(Note(lane, self.note_speed))
            self.timer = 0
            # Slowly increase difficulty
            if self.spawn_rate > 20: self.spawn_rate -= 0.05

        # Update Notes
        for note in self.notes: note.update()
        
        # Miss Logic
        for note in self.notes:
            if note.active and note.y > SCREEN_HEIGHT + 20:
                note.active = False
                self.combo = 0
                self.feedback = "MISS"
                self.feedback_timer = 20
                self.sound.play("miss")

        self.notes = [n for n in self.notes if n.active]

        # Input Handling
        if self.is_fist and not self.last_fist_state:
            self.check_hit()
        
        self.last_fist_state = self.is_fist
        if self.feedback_timer > 0: self.feedback_timer -= 1

    def draw(self):
        self.screen.fill(BLACK)
        
        # --- MENU DRAW ---
        if self.state == "MENU":
            title = self.font.render("SELECT DIFFICULTY", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            
            # Helper to draw button
            def draw_btn(rect, color, text):
                # Highlight if hovering
                if rect.collidepoint(self.hand_x, self.hand_y):
                    pygame.draw.rect(self.screen, WHITE, rect, 4)
                pygame.draw.rect(self.screen, color, rect, border_radius=15)
                t = self.font.render(text, True, BLACK)
                self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

            draw_btn(pygame.Rect(200, 200, 400, 80), GREEN, "SLOW")
            draw_btn(pygame.Rect(200, 300, 400, 80), YELLOW, "MEDIUM")
            draw_btn(pygame.Rect(200, 400, 400, 80), RED, "FAST")

            # Cursor
            pygame.draw.circle(self.screen, WHITE, (int(self.hand_x), int(self.hand_y)), 10)
            pygame.display.flip()
            return

        # --- GAME DRAW ---
        
        # Draw Lanes
        for i in range(4):
            x = 100 + (i * 200)
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 2)
            
            color = COLORS[i]
            if i == self.active_lane:
                s = pygame.Surface((200, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((*color, 30))
                self.screen.blit(s, (i * 200, 0))
                
                pygame.draw.circle(self.screen, color, (x, self.hit_y), 40)
                pygame.draw.circle(self.screen, WHITE, (x, self.hit_y), 45, 4)
            else:
                pygame.draw.circle(self.screen, color, (x, self.hit_y), 35, 2)
                pygame.draw.circle(self.screen, GRAY, (x, self.hit_y), 40, 2)

        for note in self.notes: note.draw(self.screen)

        score_t = self.font.render(f"Score: {self.score}", True, WHITE)
        combo_t = self.font.render(f"Combo: {self.combo}", True, YELLOW)
        self.screen.blit(score_t, (20, 20))
        self.screen.blit(combo_t, (20, 70))

        if self.feedback_timer > 0:
            col = RED if self.feedback == "MISS" else GREEN
            fb = self.score_font.render(self.feedback, True, col)
            self.screen.blit(fb, (SCREEN_WIDTH//2 - fb.get_width()//2, SCREEN_HEIGHT//2))

        # Cursor (Locked to Y=50 in game mode to indicate hand position)
        pygame.draw.circle(self.screen, WHITE, (int(self.hand_x), 50), 10)
        
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