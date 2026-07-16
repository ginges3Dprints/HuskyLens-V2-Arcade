# 🎮 HuskyLens Arcade Control System
---
join my discord if you need help or want to see more projects that aint here yet. https://discord.gg/Mv6mRAYqVP
---
A Python-based arcade game suite controlled by hand gestures using an ESP32 and DFRobot HuskyLens. 
This project replaces mouse/keyboard inputs with AI-powered vision tracking, 
allowing you to play games by waving your hand and making a fist.

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
9.  **Subway** for this to work you need to open subway surf in your browser an then Subway.py or run it from the launcher (very hard to play but lookin to make it better)
10.  **hill climb** for this to work you need to open hill climb in your browser an then hill_clim.py or run it from the launcher (hard to start but easy when do right)
11.  **fruit ninja** for this to work you need to open fruit ninja in your browser an then fruit_ninja.py (not tested yet)

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

📦 Installation & Setup  
1. Flash the ESP32  
Open main_esp32/main_esp32.ino in Arduino IDE.  

Install the DFRobot_HuskyLens library.  

Upload code to your ESP32.  

2. Install Python Libraries  
Open a terminal in the folder and run:  

Bash
pip install pygame pyserial
3. Fix the COM Port (IMPORTANT)  
Plug in your ESP32.

Run the fixer script:

Bash
python fix_ports.py
It will detect your ESP32 and automatically update ALL game files to use the correct port.

🚀 How to Play
You have two options to launch the Arcade:

Option A: Running from Source
If you are developing or testing, run the launcher directly with Python:

Bash
python HuskyArcade.py
Option B: Using the Arcade Executable (Plug & Play)
If you have built the application into an executable, simply double-click HuskyArcade.exe.

Note: Ensure all game files (.py) and assets are in the same folder as the .exe for everything to load correctly.

Navigation:

Move your hand up/down to scroll through the game menu.

Select: Make a FIST to launch the selected game.

Exit Game: Press ESC or close the game window to return to the launcher.

🐛 Troubleshooting
Game Not Loading? Ensure that all game files (.py) are located in the same folder as HuskyArcade.exe.

Game crashes immediately: Run python fix_ports.py again to ensure the COM port is correct.  

Hand jittery: Ensure good lighting. Avoid backlighting (don't sit with a window behind you).  

"Permission Denied": Close any other programs (like Arduino Serial Monitor) that might be using the ESP32.
📝 License
Open Source. Built for education and fun!

