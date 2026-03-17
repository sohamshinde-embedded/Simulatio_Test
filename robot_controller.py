#include <AccelStepper.h>

// --- PIN SETUP ---
// Change these to match your actual wiring!
const int stepX = 12, dirX = 13;
const int stepY = 14, dirY = 27;
const int stepZ = 26, dirZ = 25;
const int vacuumRelayPin = 2;

// NEW: Conveyor Belt Pins (Change these to your available ESP32 pins)
const int stepC = 5, dirC = 18;

// --- STEPPER CONFIG ---
AccelStepper stepX_motor(1, stepX, dirX);
AccelStepper stepY_motor(1, stepY, dirY);
AccelStepper stepZ_motor(1, stepZ, dirZ);

// NEW: Conveyor Stepper Object
AccelStepper stepC_motor(1, stepC, dirC);

// Calibration
float stepsPerMM = 80.0; 

// NEW: Conveyor Speed (Steps per second). Adjust this to match your Python BELT_SPEED!
float conveyorSpeedSteps = 1000.0; 

void setup() {
  Serial.begin(115200);
  
  // CRITICAL: 5ms timeout so the serial buffer doesn't freeze the motors
  Serial.setTimeout(5); 
  
  pinMode(vacuumRelayPin, OUTPUT);
  digitalWrite(vacuumRelayPin, LOW); // Start with vacuum off
  
  // High-Speed settings for the Robot Arm
  float maxSpeed = 3000.0;
  float highAccel = 5000.0; 

  stepX_motor.setMaxSpeed(maxSpeed); stepX_motor.setAcceleration(highAccel);
  stepY_motor.setMaxSpeed(maxSpeed); stepY_motor.setAcceleration(highAccel);
  stepZ_motor.setMaxSpeed(maxSpeed); stepZ_motor.setAcceleration(highAccel);

  // NEW: Configure Conveyor Belt Motor
  stepC_motor.setMaxSpeed(5000.0); // Allow high top speed
  stepC_motor.setSpeed(0);         // Start with belt stopped

  Serial.println("ESP32_READY");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("MOVE")) {
      // Parse "MOVE X,Y,Z"
      int comma1 = cmd.indexOf(',');
      int comma2 = cmd.indexOf(',', comma1 + 1);
      
      float x = cmd.substring(5, comma1).toFloat();
      float y = cmd.substring(comma1 + 1, comma2).toFloat();
      float z = cmd.substring(comma2 + 1).toFloat();
      
      stepX_motor.moveTo(x * stepsPerMM); 
      stepY_motor.moveTo(y * stepsPerMM); 
      stepZ_motor.moveTo(z * stepsPerMM);
    } 
    else if (cmd == "SUCK_ON") {
      digitalWrite(vacuumRelayPin, HIGH);
    } 
    else if (cmd == "SUCK_OFF") {
      digitalWrite(vacuumRelayPin, LOW);
    } 
    else if (cmd == "HOME") { 
      stepX_motor.moveTo(0); 
      stepY_motor.moveTo(0); 
      stepZ_motor.moveTo(0); 
    }
    // ==========================================
    // NEW: CONVEYOR BELT COMMANDS
    // ==========================================
    else if (cmd == "BELT_ON") {
      // Sets a constant velocity (steps per second)
      stepC_motor.setSpeed(conveyorSpeedSteps);
      Serial.println("ACK: BELT RUNNING");
    }
    else if (cmd == "BELT_OFF") {
      stepC_motor.setSpeed(0);
      Serial.println("ACK: BELT STOPPED");
    }
  }
  
  // Keep the robot arm stepping to target positions
  stepX_motor.run(); 
  stepY_motor.run(); 
  stepZ_motor.run();
  
  // NEW: Keep the conveyor belt spinning at constant velocity
  // Notice we use runSpeed() instead of run()!
  stepC_motor.runSpeed(); 
}