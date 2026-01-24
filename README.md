# 🎮 HuskyLens Arcade Control System

A Python-based arcade game suite controlled by hand gestures using an ESP32 and DFRobot HuskyLens. This project replaces mouse/keyboard inputs with AI-powered vision tracking, allowing you to play games by waving your hand and making a fist.

## ✨ Features

* **Hand Tracking:** Real-time coordinate mapping from HuskyLens to Screen.
* **Gesture Control:**
    * **Open Hand:** Move Cursor / Paddle / Bird.
    * **Fist:** Click / Shoot / Flap / Restart Game.
* **Auto-Port Fixer:** Includes a script to automatically find your ESP32 port.
* **Leaderboards:** Saves high scores locally for every game.
* **Audio Generation:** Procedural sound effects (no external MP3s required).

## 🕹️ Included Games

1.  **Space Dodge V7:** Endless shooter. Gain points by surviving and destroying rocks. Includes "Survival Score" (points for time alive) and High Score saving.
2.  **Flappy Hand V4:** Flap your wings by making a fist. Features a "Hover Ready" mode and **Gesture Restart** (Make a fist to retry).
3.  **Husky Pop V2:** Satisfying bubble popper. Includes "Chaos Power-ups" (Nukes, Giant Needles, Slow Mo) and generated sound effects.
4.  **Husky Tac Toe V2:** Play against AI or a friend (2-Player Mode). Includes turn indicators and touch-free menu selection.
5.  **Husky Dance V2:** Rhythm game with 3 Difficulty Levels (Slow, Medium, Fast). Hit notes by making a fist to the beat.
6.  **Husky Breaker:** Brick breaker with a built-in calibration mode. Move the paddle freely to test tracking before launching the ball.
7.  **Husky Hammer:** Classic Whack-a-Mole.

## 🛠️ Hardware Requirements

* **ESP32 Board** (e.g., C3 SuperMini or DevKit V1)
* **DFRobot HuskyLens** (AI Vision Sensor)
* **PC** running Windows (Python 3.x)
* **USB Cable** (Data capable)

### Wiring (I2C Connection)

| HuskyLens | ESP32 Pin |
| :--- | :--- |
| **VCC** | **5V / 3.3V** |
| **GND** | **GND** |
| **SDA** | **GPIO 8** (or standard SDA) |
| **SCL** | **GPIO 9** (or standard SCL) |

> **Setup Note:** Ensure HuskyLens "Protocol" setting is set to **I2C**.

## 📦 Installation & Setup

### 1. Flash the ESP32
1.  Open `main_esp32/main_esp32.ino` in Arduino IDE.
2.  Install the **DFRobot_HuskyLens** library.
3.  Upload code to your ESP32.

### 2. Install Python Libraries
Open a terminal in the folder and run:
```bash
pip install pygame pyserial
```
Here is exactly what should be in your folder when you upload it to GitHub, followed by the fully updated README.md.

📂 What Should Be In Your Folder?
Your game folder should look like this. Make sure you delete any old versions (like space_game_v5.py) so it looks clean.

Plaintext

HuskyLens_Arcade/
│
├── main_esp32/                 <-- Folder for Arduino code
│   └── main_esp32.ino          <-- The code you uploaded to the ESP32
│
├── launcher.py                 <-- The main menu to launch games
├── fix_ports.py                <-- The script to fix COM ports automatically
├── test_tracking.py            <-- The visualizer tool to test camera
│
├── space_game_v7.py            <-- Space Game (Survival Score + Bonus)
├── flappy_hand_v4.py           <-- Flappy Hand (Gesture Restart)
├── bubble_pop_v2.py            <-- Husky Pop (Sounds + Powerups)
├── tictactoe_v2.py             <-- Tic Tac Toe (2 Player + AI)
├── husky_dance_v2.py           <-- Dance Game (Difficulty Menu)
├── husky_breaker.py            <-- Brick Breaker (Calibration Mode)
├── hammer_game.py              <-- Whack-a-Mole (Slower/Easier)
│
├── README.md                   <-- The text file below
└── requirements.txt            <-- Optional (list of libraries: pygame, pyserial)
Note: You do not need to upload the __pycache__ folder or the .json score files (the game will create score files automatically if they are missing).

📝 New README.md
Create a file named README.md, delete everything in it, and paste this:

Markdowns

# 🎮 HuskyLens Arcade Control System

A Python-based arcade game suite controlled by hand gestures using an ESP32 and DFRobot HuskyLens. This project replaces mouse/keyboard inputs with AI-powered vision tracking, allowing you to play games by waving your hand and making a fist.

## ✨ Features

* **Hand Tracking:** Real-time coordinate mapping from HuskyLens to Screen.
* **Gesture Control:**
    * **Open Hand:** Move Cursor / Paddle / Bird.
    * **Fist:** Click / Shoot / Flap / Restart Game.
* **Auto-Port Fixer:** Includes a script to automatically find your ESP32 port.
* **Leaderboards:** Saves high scores locally for every game.
* **Audio Generation:** Procedural sound effects (no external MP3s required).

## 🕹️ Included Games

1.  **Space Dodge:** Endless shooter. Gain points by surviving and destroying rocks. Includes "Survival Score" (points for time alive) and High Score saving.
2.  **Flappy Hand:** Flap your wings by making a fist. Features a "Hover Ready" mode and **Gesture Restart** (Make a fist to retry).
3.  **Husky Pop:** Satisfying bubble popper. Includes "Chaos Power-ups" (Nukes, Giant Needles, Slow Mo) and generated sound effects.
4.  **Husky Tac Toe:** Play against AI or a friend (2-Player Mode). Includes turn indicators and touch-free menu selection.
5.  **Husky Dance:** Rhythm game with 3 Difficulty Levels (Slow, Medium, Fast). Hit notes by making a fist to the beat.
6.  **Husky Breaker:** Brick breaker with a built-in calibration mode. Move the paddle freely to test tracking before launching the ball.
7.  **Husky Hammer:** Classic Whack-a-Mole.
8.  **angry birds game** for this game credit goes to Skicheng on github https://github.com/Skicheng/Huskylens2_angry_birds_game/tree/main
9.  **Subway** for this to work you need to open subway surf in your browersan the Subway.py or run it from the launcher (very hard to play but lookin to make it better)
10.  **hill climb** for this to work you need to open hill climb in your browersan the hill_clim.py or run it from the launcher (hard to start but easy when do right)
11.  **fruit ninja** for this to work you need to open fruit ninja in your browersan the fruit_ninja.py (not tested yet)

## 🛠️ Hardware Requirements

* **ESP32 Board** (e.g., C3 SuperMini or DevKit V1)
* **DFRobot HuskyLens** (AI Vision Sensor)
* **PC** running Windows (Python 3.x)
* **USB Cable** (Data capable)

### Wiring (I2C Connection)

| HuskyLens | ESP32 Pin |
| :--- | :--- |
| **VCC** | **5V / 3.3V** |
| **GND** | **GND** |
| **SDA** | **GPIO 8** (or standard SDA) |
| **SCL** | **GPIO 9** (or standard SCL) |

> **Setup Note:** Ensure HuskyLens "Protocol" setting is set to **I2C**.

## 📦 Installation & Setup

### 1. Flash the ESP32
1.  Open `main_esp32/main_esp32.ino` in Arduino IDE.
2.  Install the **DFRobot_HuskyLens** library.
3.  Upload code to your ESP32.

### 2. Install Python Libraries
Open a terminal in the folder and run:
```bash
pip install pygame pyserial
```
3. Fix the COM Port (IMPORTANT)
Your laptop might not use "COM12". We have a script to fix this automatically!

 1.Plug in your ESP32.
 2.Run the fixer script:

  ```bash
  python fix_ports.py
  ```
It will detect your ESP32 and automatically update ALL game files to use the correct port.

4. Test Tracking
Run the visualizer to make sure your hand is detected correctly:
  ```bash
   python test_tracking.py
  ```
Green Dot: Open Hand

Red Dot: Fist detected

Ensure you can reach all 4 corners of the white box.

🚀 How to Play
Run the main launcher to pick a game:
   ```bash
   python launcher.py
   ```
Navigation: Move hand up/down to scroll.

Select: Make a FIST to launch the selected game.

Exit Game: Press ESC or close the window to return to the launcher.

🐛 Troubleshooting
Game crashes immediately: Run python fix_ports.py again to ensure the COM port is correct.
Hand jittery: Ensure good lighting. Avoid backlighting (don't sit with a window behind you).

"Permission Denied": Close any other programs (like Arduino Serial Monitor) that might be using the ESP32.

📝 License
Open Source. Built for education and fun!
