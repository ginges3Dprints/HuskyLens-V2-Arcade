#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
#
# Support module for HuskyArcade

import sys
import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
import serial.tools.list_ports

import HuskyArcade

_debug = True 

def main(*args):
    '''Main entry point for the application.'''
    # High-DPI Fix: Ensures the compiled .exe is the correct size
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass

    global root
    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    global _top1, _w1
    _top1 = root
    _w1 = HuskyArcade.Toplevel1(_top1)
    
    init(_top1, _w1)
    root.mainloop()

def init(top, gui, *args, **kwargs):
    '''This runs the moment the GUI opens.'''
    global w, top_level, root
    w = gui
    top_level = top
    root = top
    
    # --- 1. LINK ALL BUTTONS TO FUNCTIONS ---
    w.btn_Dodge.configure(command=on_btn_Dodge)
    w.btn_Hands.configure(command=on_btn_Hands)
    w.btn_pop.configure(command=on_btn_pop)
    w.Btn_TacToe.configure(command=on_btn_TacToe)
    w.btn_Dance.configure(command=on_btn_Dance)
    w.btn_Braker.configure(command=on_btn_Braker)
    w.btn_Hammer.configure(command=on_btn_Hammer)
    w.btn_Camera.configure(command=on_btn_Camera)
    w.btn_Exit.configure(command=on_btn_Exit)
    
    # --- 2. AUTO-DETECT COM PORTS ---
    ports = [port.device for port in serial.tools.list_ports.comports()]
    
    # Populate TCombobox_PortSelector
    w.TCombobox_PortSelector['values'] = ports
    
    if ports:
        w.TCombobox_PortSelector.set(ports[0])
        w.Label_Connected.configure(text=f"Ready: {ports[0]}", foreground="green")
    else:
        w.TCombobox_PortSelector.set("No Ports Found")
        w.Label_Connected.configure(text="Disconnected", foreground="red")

def launch_game(script_name):
    '''Helper function to pass COM port and launch target python scripts.'''
    selected_port = w.TCombobox_PortSelector.get()
    
    if selected_port == "No Ports Found" or selected_port == "":
        w.Label_Connected.configure(text="Select COM port!", foreground="red")
        return
        
    w.Label_Connected.configure(text=f"Running {script_name}...", foreground="cyan")
    
    # Store selected port in environment variable
    os.environ["HUSKY_PORT"] = selected_port
    
    # Minimize launcher while playing
    root.iconify() 
    
    # Launch game using "python" directly to prevent PyInstaller looping
    subprocess.run(["python", script_name])
    
    # Bring launcher back up when game closes
    root.deiconify()
    w.Label_Connected.configure(text=f"Ready: {selected_port}", foreground="green")

# --- BUTTON CLICK HANDLERS ---

def on_btn_Dodge(*args):
    launch_game("space_game.py")

def on_btn_Hands(*args):
    launch_game("flappy_hand.py")

def on_btn_pop(*args):
    launch_game("bubble_pop.py")

def on_btn_TacToe(*args):
    launch_game("tictactoe.py")

def on_btn_Dance(*args):
    launch_game("dance_game.py")

def on_btn_Braker(*args):
    launch_game("breaker.py")

def on_btn_Hammer(*args):
    launch_game("hammer_game.py")

def on_btn_Camera(*args):
    if os.path.exists("test_tracking.py"):
        launch_game("test_tracking.py")
    else:
        launch_game("debug_husky.py")

def on_btn_Exit(*args):
    print("Closing Arcade...")
    sys.exit()

if __name__ == '__main__':
    main()