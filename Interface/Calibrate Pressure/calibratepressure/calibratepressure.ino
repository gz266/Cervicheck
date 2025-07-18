#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP4725.h>
#include "AD5933.h"
#include <SD.h>

Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

#define DAC_RESOLUTION (9)
char userInput;
// AD5933 Constants

#define START_FREQ (10000)
#define FREQ_INCR (10000)
#define NUM_INCR (2)
#define REF_RESIST (300)

// Pressure Constants
// 12% gel: test -2 increment, 21 increases
// 7.5% gel: test -1 increment, 30 increases
#define PRES_START (-1)
#define PRES_INCR (-1)
#define PRES_NUM_INCR (35)

double gain[NUM_INCR + 1];
int phase[NUM_INCR + 1];

int i;

int sL[3] = { 8, 9, 10 };
// First value corresponds to 300 ohm resistor
// Green: 560 vs non-Green 270
// int MUXtable[8][3] = { { 1, 1, 0 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 1 } };  // purple board
// int MUXtable[8][3] = { { 1, 0, 1 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 1, 0 }, { 1, 1, 1 } }; // green board
// int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 1 }, { 0, 1, 1 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 0, 0, 0 }, { 1, 1, 0 } }; // new pad arrangement
// Flipped new pad arrangement, if pads are flipped
int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 0 }, { 0, 0, 0 }, { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 }, { 0, 1, 1 }, { 1, 1, 1 } };

int curPad = 1;
float stressStrain[7] = {0,0,0,0,0,0,0};

int rampTime[PRES_NUM_INCR];
int rampTimeInitial = 0;
int rampTimeFinal = 0;
int collectionTime[PRES_NUM_INCR];
int collectionTimeInitial = 0;
int collectionTimeFinal = 0;

int sweeptime;

// Board Constants
const int yellowLED = 7;
const int greenLED = 6;
const int startbuttonPin = 5;
int startbuttonState = 0;

float pressure;

// Pressure Control Constants
// y = mx where y is digital value to supply DAC and x is desired pressure (-kPa)
const float slope = -86.50;
const float yint = 	56.54;
const float error = 0.05;

void setup(void) {
  Serial.begin(9600);
  Wire.begin();                    //  setup serial
  // LEDs
  startbuttonState = digitalRead(startbuttonPin);
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize MUX
  for (i = 0; i < 3; i++) {
    pinMode(sL[i], OUTPUT);
  }

  Serial.print("Initializing... ");
  // Perform initial configuration. Fail if any one of these fail.
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(START_FREQ) && AD5933::setIncrementFrequency(FREQ_INCR) && AD5933::setNumberIncrements(NUM_INCR) && AD5933::setPGAGain(PGA_GAIN_X1) )) {
    Serial.println("FAILED in initialization!");
    while (true);
  }

  Serial.println("Initialized!");

  // Select 300 OHM resistor
  selectPad(0);

  Serial.print("Calibrating... ");
  // Perform calibration sweep
  if (!AD5933::calibrate(gain, phase, REF_RESIST, NUM_INCR + 1)) {
    Serial.println("Calibration failed...");
    while (true);
  }
  Serial.println("Calibrated!");

  // Initialize ADC
  // ADC range is +/- 6.144 V (1 bit = 3 mV)
  ads1015.begin(0x48);

  // Initialize DAC
  dac.begin(0x60);

  // Initialize Array
  for (int i = 0; i < PRES_NUM_INCR; i++) {
    rampTime[i] = 0;
    collectionTime[i] = 0;
  } 
}

void loop(void) {
  dac.setVoltage(0, false);
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, HIGH);
    
  if(Serial.available()>0){
    userInput = Serial.read();               // read user input
    if(userInput == 'p'){         
      digitalWrite(greenLED, HIGH);
      digitalWrite(yellowLED, LOW);
      delay(1000);
      long t1 = millis();
      calibratePressure();
      long t2 = millis();
    }
  }
} // Void Loop
    

void calibratePressure() {
  Serial.println("50");
  Serial.println("100");
  Serial.println("150");
  Serial.println("200");
  Serial.println("250");
  Serial.println("500");
  Serial.println("1000");
  Serial.println("1500");
  Serial.println("2000");
  Serial.println("2500");
  Serial.println("3000");
  Serial.println("3500");
  for (int i = 50; i < 251; i+=50){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
  for (int i = 500; i < 3501; i+=500){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
}
void selectPad(int p) {
  // Pad 0 is calibration resistor, Pad 1-7 are on flex pcb
  digitalWrite(sL[0], MUXtable[p][0]);
  digitalWrite(sL[1], MUXtable[p][1]);
  digitalWrite(sL[2], MUXtable[p][2]);
}
// Pressure Control Functions
float getPressure(void) {
  /*
    Returns pressure from the MPXV5050VC6T1 pressure sensor

    Paramters: None
    Returns: takes in voltage reading from sensor from the ADS1015 pressure sensor and returns kPa
    PRESSURE READING DEPENDS ON THE VOLTAGE SUPPLIED (I TESTED FOR LIKE 2 MONTHS WITHOUT REALIZING!!!)
    - Hence, second channel on the ADS1015 tracks the voltage supplied

    With testing from timing, function takes 2 milliseconds to run
  */

  // int16_t adc0; float vout; float pressure;
  // adc0 = ads1015.readADC_SingleEnded(0);         // output in bits, from A0
  // vout = ((adc0 * 3.0) / 1000);    // Convert bits to voltage, found on ADS1015 data sheet
  // pressure = (vout-(0.92*5))/(0.018*5);    // Convert voltage to pressure, found on MPXV5050VC6T1 data sheet
  // voltage supply changes when battery turns on! For 18V, 0.8A -> vs is 4.58 V
  return (((ads1015.readADC_SingleEnded(0) * 3.0) / 1000) - (0.92 * ((ads1015.readADC_SingleEnded(2) * 3.0) / 1000))) / (0.018 * ((ads1015.readADC_SingleEnded(2) * 3.0) / 1000));
}

