import pygame
import serial
import serial.tools.list_ports
import json
import random
import sys
import time

# --- CONFIGURATION ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700 
FPS = 60

# Colors
BG_COLOR = (20, 20, 30)
WHITE = (255, 255, 255)   # <--- THIS WAS MISSING!
LINE_COLOR = (255, 255, 255)
X_COLOR = (255, 50, 50)  # Red
O_COLOR = (50, 100, 255) # Blue
CURSOR_COLOR_X = (255, 100, 100) 
CURSOR_COLOR_O = (100, 100, 255)
BUTTON_COLOR = (50, 50, 70)
BUTTON_HOVER = (80, 80, 100)

CAM_W = 320

def find_port():
    return "COM8" 

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Husky Tac Toe V2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 80, bold=True)
        self.msg_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 30)
        
        self.port = find_port()
        self.ser = None
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 115200, timeout=0.05)
                self.ser.dtr = True
                self.ser.rts = True
            except: pass

        # Hand Tracking Variables
        self.hand_x = SCREEN_WIDTH // 2
        self.hand_y = SCREEN_HEIGHT // 2
        self.is_fist = False
        self.was_fist = False 

        # Game State
        self.state = "MENU" # MENU, PLAYING, GAMEOVER
        self.game_mode = "AI" # AI or PVP
        self.reset_board()

    def reset_board(self):
        # 3x3 Grid (0 = Empty, 1 = X, 2 = O)
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.turn = 1 # 1 for X, 2 for O
        self.winner = 0 
        self.game_over = False

    def check_winner(self):
        b = self.board
        lines = [
            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)], # Rows
            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)], # Cols
            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)] # Diagonals
        ]
        
        for line in lines:
            p1 = b[line[0][0]][line[0][1]]
            p2 = b[line[1][0]][line[1][1]]
            p3 = b[line[2][0]][line[2][1]]
            if p1 != 0 and p1 == p2 and p2 == p3: return p1
        
        # Draw check
        if all(0 not in row for row in b): return 3 
        return 0

    def ai_move(self):
        # Find empty spots
        empty = [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == 0]
        
        if empty:
            # Draw "Thinking" state briefly
            self.draw()
            pygame.display.flip()
            time.sleep(0.5)
            
            # Pick Move
            r, c = random.choice(empty)
            self.board[r][c] = 2
            
            # Check Result
            win = self.check_winner()
            if win != 0:
                self.winner = win
                self.state = "GAMEOVER"
            else:
                self.turn = 1

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

        # --- MENU LOGIC ---
        if self.state == "MENU":
            # Check Buttons
            btn1 = pygame.Rect(100, 300, 400, 100)
            btn2 = pygame.Rect(100, 450, 400, 100)
            
            cursor = pygame.Rect(self.hand_x, self.hand_y, 1, 1)
            
            if self.is_fist and not self.was_fist:
                if cursor.colliderect(btn1):
                    self.game_mode = "AI"
                    self.reset_board()
                    self.state = "PLAYING"
                elif cursor.colliderect(btn2):
                    self.game_mode = "PVP"
                    self.reset_board()
                    self.state = "PLAYING"
        
        # --- GAMEPLAY LOGIC ---
        elif self.state == "PLAYING":
            # Grid Logic
            cw = SCREEN_WIDTH / 3
            ch = (SCREEN_HEIGHT - 100) / 3 # Subtract top bar space
            
            grid_x = int(self.hand_x // cw)
            grid_y = int((self.hand_y - 100) // ch) # Offset by 100 for top bar
            
            # Only allow moves inside the grid
            if 0 <= grid_x <= 2 and 0 <= grid_y <= 2:
                if self.is_fist and not self.was_fist:
                    if self.board[grid_y][grid_x] == 0:
                        
                        # --- PLAYER 1 TURN (X) ---
                        if self.turn == 1:
                            self.board[grid_y][grid_x] = 1
                            win = self.check_winner()
                            if win != 0:
                                self.winner = win
                                self.state = "GAMEOVER"
                            else:
                                self.turn = 2
                                if self.game_mode == "AI":
                                    self.ai_move()

                        # --- PLAYER 2 TURN (O) --- (Only in PVP)
                        elif self.turn == 2 and self.game_mode == "PVP":
                            self.board[grid_y][grid_x] = 2
                            win = self.check_winner()
                            if win != 0:
                                self.winner = win
                                self.state = "GAMEOVER"
                            else:
                                self.turn = 1

        # --- GAMEOVER LOGIC ---
        elif self.state == "GAMEOVER":
            if self.is_fist and not self.was_fist:
                self.state = "MENU"

        self.was_fist = self.is_fist

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # --- MENU DRAW ---
        if self.state == "MENU":
            title = self.font.render("HUSKY TOE", True, LINE_COLOR)
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            
            # Button 1
            btn1 = pygame.Rect(100, 300, 400, 100)
            col1 = BUTTON_HOVER if btn1.collidepoint(self.hand_x, self.hand_y) else BUTTON_COLOR
            pygame.draw.rect(self.screen, col1, btn1, border_radius=20)
            t1 = self.msg_font.render("1 PLAYER (AI)", True, WHITE)
            self.screen.blit(t1, (btn1.centerx - t1.get_width()//2, btn1.centery - t1.get_height()//2))

            # Button 2
            btn2 = pygame.Rect(100, 450, 400, 100)
            col2 = BUTTON_HOVER if btn2.collidepoint(self.hand_x, self.hand_y) else BUTTON_COLOR
            pygame.draw.rect(self.screen, col2, btn2, border_radius=20)
            t2 = self.msg_font.render("2 PLAYERS", True, WHITE)
            self.screen.blit(t2, (btn2.centerx - t2.get_width()//2, btn2.centery - t2.get_height()//2))

        # --- GAME DRAW ---
        else:
            # Top Info Bar
            bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 100)
            pygame.draw.rect(self.screen, (30, 30, 40), bar_rect)
            
            if self.state == "PLAYING":
                if self.turn == 1:
                    txt = "PLAYER 1 (X) TURN"
                    col = X_COLOR
                else:
                    txt = "COMPUTER TURN" if self.game_mode == "AI" else "PLAYER 2 (O) TURN"
                    col = O_COLOR
                
                info = self.msg_font.render(txt, True, col)
                self.screen.blit(info, (SCREEN_WIDTH//2 - info.get_width()//2, 30))

            # Draw Grid
            offset_y = 100
            cw = SCREEN_WIDTH / 3
            ch = (SCREEN_HEIGHT - offset_y) / 3
            
            pygame.draw.line(self.screen, LINE_COLOR, (cw, offset_y), (cw, SCREEN_HEIGHT), 5)
            pygame.draw.line(self.screen, LINE_COLOR, (cw*2, offset_y), (cw*2, SCREEN_HEIGHT), 5)
            pygame.draw.line(self.screen, LINE_COLOR, (0, offset_y + ch), (SCREEN_WIDTH, offset_y + ch), 5)
            pygame.draw.line(self.screen, LINE_COLOR, (0, offset_y + ch*2), (SCREEN_WIDTH, offset_y + ch*2), 5)

            # Draw Pieces
            for r in range(3):
                for c in range(3):
                    cx = c * cw + cw/2
                    cy = r * ch + ch/2 + offset_y
                    
                    if self.board[r][c] == 1: # X
                        pygame.draw.line(self.screen, X_COLOR, (cx-40, cy-40), (cx+40, cy+40), 10)
                        pygame.draw.line(self.screen, X_COLOR, (cx+40, cy-40), (cx-40, cy+40), 10)
                    elif self.board[r][c] == 2: # O
                        pygame.draw.circle(self.screen, O_COLOR, (int(cx), int(cy)), 50, 8)

            # Draw Winner Overlay
            if self.state == "GAMEOVER":
                over_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                over_s.fill((0, 0, 0, 200))
                self.screen.blit(over_s, (0,0))
                
                if self.winner == 1: msg, c = "PLAYER 1 WINS!", X_COLOR
                elif self.winner == 2: msg, c = ("COMPUTER WINS!" if self.game_mode == "AI" else "PLAYER 2 WINS!"), O_COLOR
                else: msg, c = "IT'S A DRAW!", WHITE
                
                win_t = self.font.render(msg, True, c)
                sub_t = self.msg_font.render("Fist to Menu", True, WHITE)
                
                self.screen.blit(win_t, (SCREEN_WIDTH//2 - win_t.get_width()//2, 250))
                self.screen.blit(sub_t, (SCREEN_WIDTH//2 - sub_t.get_width()//2, 350))

        # --- CURSOR ---
        cursor_col = CURSOR_COLOR_X
        if self.state == "PLAYING" and self.turn == 2:
            cursor_col = CURSOR_COLOR_O
        
        pygame.draw.circle(self.screen, cursor_col, (int(self.hand_x), int(self.hand_y)), 10)
        pygame.draw.circle(self.screen, WHITE, (int(self.hand_x), int(self.hand_y)), 12, 2)

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