// V1: Contains pressure control, full impedance sweeps with all 7 pads, and data collection
// Does not contain fully automated impedance sweeps across pressures!

#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP4725.h>
#include "AD5933.h"
#include <SD.h>


Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

#define DAC_RESOLUTION (9)

// AD5933 Constants

#define START_FREQ (5000)
#define FREQ_INCR (1000)
#define NUM_INCR (7)
#define REF_RESIST (300)

double gain[NUM_INCR + 1];
int phase[NUM_INCR + 1];

int i;
int sL[3] = { 8, 9, 10 };
// First value corresponds to 300 ohm resistor
// Green: 560 vs non-Green 270
// int MUXtable[8][3] = { { 1, 1, 0 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 1 } };  // purple board
//int MUXtable[8][3] = { { 1, 0, 1 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 1, 0 }, { 1, 1, 1 } }; // green board
// int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 1 }, { 1, 1, 0 }, { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 }, { 0, 0, 0 }, { 0, 1, 1 } }; // new pad arrangement WRONG
int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 1 }, { 0, 1, 1 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 0, 0, 0 }, { 1, 1, 0 } }; // new pad arrangement
// Board Constants

const int yellowLED = 5;
const int greenLED = 6;
const int startbuttonPin = 7;
int startbuttonState = 0;

// Pressure Control Constants
// y = mx where y is digital value to supply DAC and x is desired pressure (-kPa)
const int slope = -80;

//SD Card
File dataFile;
String filename = "Data.csv";
const int chipSelectPin = 4;
int cur;

void setup(void) {
  Serial.begin(9600);
  Wire.begin();

  // LEDs
  startbuttonState = digitalRead(startbuttonPin);
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);

  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize SD Card
  if (SD.begin(chipSelectPin)) {
    Serial.println("SD card module is connected.");
  } else {
    Serial.println("SD card module is not detected. Check connections.");
  }

  // Open a new file for writing
  dataFile = SD.open(filename, FILE_WRITE);
  // SD.remove(filename);
  if (dataFile) {
    Serial.println("Created data.csv file.");
  } else {
    Serial.println("Failed to create data.csv file!");
  }

  dataFile.println(" ");
  dataFile.print("Freq (kHz): ");
  dataFile.print(", ");
  int cfreq = START_FREQ / 1000;
  for (int i = 0; i < NUM_INCR + 1; i++, cfreq += FREQ_INCR / 1000) {
    dataFile.print(cfreq);
    dataFile.print(", ");
  }

  dataFile.print(", ");
  dataFile.print("Pressure: ");
  dataFile.print(", ");
  dataFile.print("Duration: ");
  dataFile.close();

  // Initialize Probe Board

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

  // Recalibrate DAC, use x instead of 4095 for exact voltage values
  // Start with no vacuum pressure, use PID control to find initial value
  //dac.setVoltage((5*4095)/5, false);
}

void loop(void) {
  selectPressure(-19);

  // Lights for Ready to Test
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, HIGH);
  startbuttonState = digitalRead(startbuttonPin);
  if (startbuttonState == HIGH) {
    digitalWrite(greenLED, HIGH);
    digitalWrite(yellowLED, LOW);
    dataFile = SD.open(filename, FILE_WRITE);
    for (int i = 0; i < 1; i++) {
      runSweep();
    }
    dataFile.close();
    Serial.println("Done!");
  }
  /*
  Serial.print("L:");
  Serial.print(0);
  Serial.print(", ");

  Serial.print("H:");
  Serial.print(-10);
  Serial.print(", ");
  
  Serial.print("Current Pressure:");
  Serial.println(getPressure());
  */
}

void selectPressure(float pressure) {
  /*
  float error = pressure - getPressure();
  if (error < 1){
    dac.setVoltage(4095, false);
  }
  */
  dac.setVoltage(slope * pressure, false);
}

void runSweep() {
  dataFile.println(" ");
  for (int i = 1; i < (sizeof(MUXtable) / sizeof(MUXtable[0])); i++) {
    dataFile.println(" ");
    dataFile.print("Pad ");
    dataFile.print(i);
    selectPad(i);

    int time1 = millis();
    frequencySweepEasy();
    int time2 = millis();

    dataFile.print(", ");
    dataFile.print(", ");
    dataFile.print(getPressure());
    dataFile.print(", ");
    dataFile.print(time2 - time1);
    Serial.print("Test time (ms): ");
    Serial.println(time2 - time1);
    Serial.print("Pressure (kPa): ");
    Serial.println(getPressure());
  }
}

void frequencySweepEasy() {
  // Create arrays to hold the data
  int real[NUM_INCR + 1], imag[NUM_INCR + 1];

  // Perform the frequency sweep
  if (AD5933::frequencySweep(real, imag, NUM_INCR + 1)) {
    // Print the frequency data
    int cfreq = START_FREQ / 1000;
    for (int i = 0; i < NUM_INCR + 1; i++, cfreq += FREQ_INCR / 1000) {
      // Print raw frequency data
      Serial.print(cfreq);
      Serial.print(": Impedance = ");
      // Serial.print(real[i]);
      // Serial.print("/I=");
      // Serial.print(imag[i]);

      // Compute impedance
      double magnitude = sqrt(pow(real[i], 2) + pow(imag[i], 2));
      double impedance = 1 / (magnitude * gain[i]);

      // Serial.print("  |Z|=");
      dataFile.print(", ");
      Serial.println(impedance);
      dataFile.print(impedance);
    }
    Serial.println("Frequency sweep complete!");
  } else {
    Serial.println("Frequency sweep failed...");
  }
}

void selectPad(int p) {
  // Pad 0 is calibration resistor, Pad 1-7 are on flex pcb
  digitalWrite(sL[0], MUXtable[p][0]);
  digitalWrite(sL[1], MUXtable[p][1]);
  digitalWrite(sL[2], MUXtable[p][2]);
}

float getPressure(void) {
  /*
    Returns pressure from the MPXV5050VC6T1 pressure sensor

    Paramters: None
    Returns: takes in voltage reading from sensor from the ADS1015 pressure sensor and returns kPa

    With testing from timing, function takes 2 milliseconds to run
  */

  // int16_t adc0; float vout; float pressure;
  // adc0 = ads1015.readADC_SingleEnded(0);         // output in bits, from A0
  // vout = ((adc0 * 3.0) / 1000);    // Convert bits to voltage, found on ADS1015 data sheet
  // pressure = (vout-(0.92*5))/(0.018*5);    // Convert voltage to pressure, found on MPXV5050VC6T1 data sheet

  return (((ads1015.readADC_SingleEnded(0) * 3.0) / 1000) - (0.92 * 5)) / (0.018 * 5);
}