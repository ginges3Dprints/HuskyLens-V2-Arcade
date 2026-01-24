import os
import re
import serial.tools.list_ports

def get_available_ports():
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

def update_files(new_port):
    # Get all python files in the current folder
    files = [f for f in os.listdir('.') if f.endswith('.py') and f != "fix_ports.py"]
    
    count = 0
    print(f"\nScanning {len(files)} files...")

    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # This Regex looks for: return "COM12" (or any number) and replaces it
            # It matches: return "COM[digits]"
            if re.search(r'return "COM\d+"', content):
                new_content = re.sub(r'return "COM\d+"', f'return "{new_port}"', content)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ Updated {filename} to use {new_port}")
                count += 1
            else:
                print(f"-------- Skipped {filename} (No hardcoded port found)")
        
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")

    print(f"\nDONE! Updated {count} files.")
    print("You can now run 'launcher.py' or your games!")

def main():
    print("--- AUTOMATIC PORT FIXER ---")
    
    # 1. Find Ports
    ports = get_available_ports()
    
    if not ports:
        print("❌ No COM ports found! Is your ESP32 plugged in?")
        return

    # 2. Show Ports
    print("\nAvailable Ports:")
    for i, p in enumerate(ports):
        print(f" [{i+1}] {p}")

    # 3. Ask User
    if len(ports) == 1:
        choice = input(f"\nOnly one port found ({ports[0]}). Use this? (y/n): ").lower()
        if choice == 'y' or choice == '':
            selected_port = ports[0]
        else:
            print("Operation cancelled.")
            return
    else:
        try:
            selection = int(input("\nEnter the number of your ESP32 port: ")) - 1
            selected_port = ports[selection]
        except:
            print("Invalid selection.")
            return

    # 4. Run the Update
    print(f"\nUpdating all games to use {selected_port}...")
    update_files(selected_port)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()