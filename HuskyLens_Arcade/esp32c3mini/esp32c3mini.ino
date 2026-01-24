#include <Wire.h>
#include "DFRobot_HuskylensV2.h"

HuskylensV2 huskylens;

// --- PINS ---
#define I2C_SDA 8
#define I2C_SCL 9

// --- IDS ---
#define ID_FACE     1
#define ID_FIST     1
#define ID_PALM     2

// --- MODES ---
enum Mode { HAND_MODE, FACE_MODE };
Mode currentMode = HAND_MODE;

// --- PHYSICS VARIABLES (Restored!) ---
bool grabbed = false;
int baseX = -1, baseY = -1;
unsigned long grabStartMs = 0;
float lastPower = 0, lastAngle = 0;

// Helper Math Function
template<typename T>
T clamp(T v, T lo, T hi) { return v < lo ? lo : (v > hi ? hi : v); }

// --- JSON HELPERS ---

// 1. Complex Data (For Angry Birds)
void sendGrabJSON(float power, float angle, int id, int x, int y) {
  Serial.print("{\"gesture\":\"grab\",\"id\":");
  Serial.print(id);
  Serial.print(",\"power\":");
  Serial.print(power, 1);
  Serial.print(",\"angle\":");
  Serial.print(angle, 4);
  Serial.print(",\"x\":");
  Serial.print(x);
  Serial.print(",\"y\":");
  Serial.print(y);
  Serial.println("}");
}

// 2. Simple Data (For Menu/Launcher)
void sendSimpleJSON(const char* g, int id, int x, int y) {
  Serial.print("{\"gesture\":\""); Serial.print(g);
  Serial.print("\",\"id\":"); Serial.print(id);
  Serial.print(",\"x\":"); Serial.print(x);
  Serial.print(",\"y\":"); Serial.print(y);
  Serial.println("}");
}

// 3. Release Data (For Shooting Birds)
void sendReleaseJSON(int id, float power, float angle) {
  Serial.print("{\"gesture\":\"release\",\"id\":");
  Serial.print(id);
  Serial.print(",\"power\":"); Serial.print(power, 1);
  Serial.print(",\"angle\":"); Serial.print(angle, 4);
  Serial.println("}");
}

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);

  while (!huskylens.begin(Wire)) {
      Serial.println("HuskyLens not found!");
      delay(500);
  }
  
  // Start in Hand Mode
  huskylens.switchAlgorithm(ALGORITHM_HAND_RECOGNITION);
}

void processFaceMode() {
  int count = huskylens.getResult(ALGORITHM_FACE_RECOGNITION);
  if (count > 0) {
    Result* r = huskylens.result[ALGORITHM_FACE_RECOGNITION][0];
    if (r->ID == ID_FACE) {
      Serial.print("{\"type\":\"face\",\"id\":");
      Serial.print(r->ID);
      Serial.println("}");
    }
  }
}

void processHandMode() {
  int count = huskylens.getResult(ALGORITHM_HAND_RECOGNITION);
  if (count == 0) return;

  // Find Objects
  Result* fistObj = nullptr;
  Result* palmObj = nullptr;

  for(int i = 0; i < count; i++) {
      Result* r = huskylens.result[ALGORITHM_HAND_RECOGNITION][i];
      if(r->ID == ID_FIST) fistObj = r;
      else if(r->ID == ID_PALM) palmObj = r;
  }

  // --- FIST LOGIC (Aiming / Dragging) ---
  if (fistObj != nullptr) {
    int x = fistObj->xCenter;
    int y = fistObj->yCenter;

    if (!grabbed) {
      grabbed = true;
      baseX = x; baseY = y;
      grabStartMs = millis();
      lastPower = 0; lastAngle = 0;
    }
    
    // MATH RESTORED HERE:
    int dx = x - baseX;
    int dy = y - baseY;
    float dist  = sqrtf((float)dx*dx + (float)dy*dy);
    float power = clamp(dist / 2.0f, 0.0f, 100.0f);
    float angle = atan2f(-dy, (float)dx);

    lastPower = power; 
    lastAngle = angle;
    
    sendGrabJSON(power, angle, ID_FIST, x, y);
    delay(30);
    return;
  }

  // --- PALM LOGIC (Menu / Release) ---
  if (palmObj != nullptr) {
    if (grabbed) {
      // We were holding a fist, now we opened hand -> SHOOT
      sendReleaseJSON(ID_PALM, lastPower, lastAngle);
      grabbed = false;
      baseX = -1; baseY = -1;
    } else {
      // Just moving cursor (Menu Mode)
      sendSimpleJSON("hand_open", ID_PALM, palmObj->xCenter, palmObj->yCenter);
    }
    delay(50);
  }
}

void loop() {
  // 1. LISTEN FOR MODE SWITCH COMMANDS
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "MODE_FACE") {
      huskylens.switchAlgorithm(ALGORITHM_FACE_RECOGNITION);
      currentMode = FACE_MODE;
      Serial.println("{\"status\":\"Switched to FACE\"}");
    }
    else if (cmd == "MODE_HAND") {
      huskylens.switchAlgorithm(ALGORITHM_HAND_RECOGNITION);
      currentMode = HAND_MODE;
      Serial.println("{\"status\":\"Switched to HAND\"}");
    }
  }

  // 2. RUN LOGIC
  if (currentMode == HAND_MODE) {
      processHandMode();
  } else {
      processFaceMode();
  }
  
  delay(20);
}