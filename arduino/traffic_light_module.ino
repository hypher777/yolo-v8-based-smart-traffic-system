/*
  Smart Traffic Light Controller - 4 Road Setup
  Compatible with Electrobot / 4-Pin LED Modules (GND, R, Y, G)
  
  Protocol:
  Receives a single byte via Serial.
  Format: (RoadNum << 4) | ColorCode
  RoadNum: 1, 2, 3, or 4
  ColorCode: 1=Green, 2=Yellow, 3=Red
*/

// --- Pin Definitions ---
// Change these if you use different pins
const int PINS[4][3] = {
  {8, 9, 10},  // Road 1: Red, Yellow, Green
  {2, 3, 4},   // Road 2: Red, Yellow, Green
  {5, 6, 7},   // Road 3: Red, Yellow, Green
  {11, 12, 13} // Road 4: Red, Yellow, Green
};

void setup() {
  Serial.begin(9600);
  
  // Initialize all pins as OUTPUT and turn them OFF
  for(int r=0; r<4; r++) {
    for(int c=0; c<3; c++) {
      pinMode(PINS[r][c], OUTPUT);
      digitalWrite(PINS[r][c], LOW);
    }
  }
  
  // Start with all roads RED
  for(int road=1; road<=4; road++) {
    updateHardware(road, 3); // 3 = Red
  }
  
  Serial.println("Traffic Controller Ready");
}

void loop() {
  if (Serial.available() > 0) {
    byte cmd = Serial.read();
    
    // Extract road and color from the byte
    int road = (cmd >> 4) & 0x0F;
    int color = cmd & 0x0F;
    
    // Update the LEDs
    if (road >= 1 && road <= 4) {
      updateHardware(road, color);
    }
  }
}

void updateHardware(int road, int colorCode) {
  int roadIdx = road - 1;
  int pinRed = PINS[roadIdx][0];
  int pinYel = PINS[roadIdx][1];
  int pinGrn = PINS[roadIdx][2];
  
  // Turn all OFF for this road first (Clear state)
  digitalWrite(pinRed, LOW);
  digitalWrite(pinYel, LOW);
  digitalWrite(pinGrn, LOW);
  
  // Turn ON the requested color
  if (colorCode == 1)      digitalWrite(pinGrn, HIGH); // Green
  else if (colorCode == 2) digitalWrite(pinYel, HIGH); // Yellow
  else if (colorCode == 3) digitalWrite(pinRed, HIGH); // Red
}
