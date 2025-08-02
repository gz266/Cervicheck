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
int pres_start = -1;
int pres_incr = -1;
int pres_num_incr = 20;

double gain[NUM_INCR + 1];
double phase[NUM_INCR + 1];

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

// Board Constants
const int yellowLED = 7;
const int greenLED = 6;
const int startbuttonPin = 5;
int startbuttonState = 0;

float pressure;

// Pressure Control Constants
// y = mx where y is digital value to supply DAC and x is desired pressure (-kPa)
float slope = -79.1919;
float yint = 36.2067;
String data;
const float error = 0.05;

//SD Card
File dataFile;
String filename = "Data.csv";
const int chipSelectPin = 2;

void setup(void) {
  Serial.begin(9600);
  Wire.begin();

  // LEDs
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);

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

  AD5933::setSettlingCycles(2047);
  // Serial.println(AD5933::readRegister(0x8A));
  // Serial.println(AD5933::readRegister(0x8B));
}

void loop(void) {
  dac.setVoltage((0*4095)/5, false);
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, HIGH);
  if(Serial.available()>0){
    userInput = Serial.read();               // read user input
    if(userInput == 's'){         
      digitalWrite(greenLED, HIGH);
      digitalWrite(yellowLED, LOW);
      long t1 = millis();
      pressureSweep();
      long t2 = millis();
      Serial.println("Done!");
      for (int i = 1; i < 8; i++) {
        Serial.println(stressStrain[i-1]);
      } 
      Serial.print("Time: ");
      Serial.println(t2-t1);
      for(int i=0; i < 7; i++){
        stressStrain[i] = 0;
      }
    }
  if(userInput == 'p'){         
      digitalWrite(greenLED, HIGH);
      digitalWrite(yellowLED, LOW);
      long t1 = millis();
      calibratePressure();
      long t2 = millis();
    }
  if(userInput == 'r'){
    data = Serial.readStringUntil('\r');
    slope = data.toFloat();
    data = Serial.readStringUntil('\r');
    yint = data.toFloat();
    }
  if(userInput == 'i'){
    data = Serial.readStringUntil('\r');
    pres_start = data.toInt();
    data = Serial.readStringUntil('\r');
    pres_incr = data.toInt();
    data = Serial.readStringUntil('\r');
    pres_num_incr = data.toInt();

    }
  }
}

void calibratePressure() {
  Serial.println("Voltage: ");
  Serial.println("50");
  Serial.println("250");
  Serial.println("500");
  Serial.println("1500");
  Serial.println("2500");
  Serial.println("Pressure: ");
  for (int i = 50; i < 251; i+=200){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
  for (int i = 500; i < 2501; i+=1000){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
  Serial.println("Done!");
}
// Testing Functions
void pressureSweep() {
  curPad = 1;
  pressure = pres_start;
  int sweep;
  for (int i = 0; i < pres_num_incr; i++, pressure += pres_incr) {
    if (curPad == 8){
      break;
    }
    if ((i < pres_num_incr + 1) == 0){
      Serial.println("Break");
      break;
    }
    // TODO Update Python to say sweeping x of y increment
    // TODO Update Python output to say that we are reaching x pressure (send pressure to Python)

    Serial.print("Sweeping at Pressure (kPa): ");
    Serial.println(pressure);
    selectPressure(pressure);

    Serial.print("Current Pressure (kPa): ");
    Serial.println(getPressure());
    int count = 0;
    // Just in case pressure is not reached
    while (abs(getPressure()-pressure) > error){
      count++;
      if (count > 200){
        break;
      }
    }
    runTest(curPad);
  }
}

void runTest(int padnum) {
  // dataFile.println(" ");
  // dataFile.print("Pad ");
  // dataFile.print(padnum);

  // TODO Send Pad and Pressure to python
  
  Serial.print("Pad ");
  Serial.print(padnum);
  Serial.println(" being tested");
  Serial.print("Pressure Tested (kPa): ");
  Serial.println(getPressure());
  
  selectPad(padnum);
  int time1 = millis();
  frequencySweepStressStrain();
  int time2 = millis();
  /*
  // dataFile.print(", ");
  // dataFile.print(", ");
  // dataFile.print(getPressure());
  dataFile.print(", ");
  dataFile.print(time2 - time1);
  */
  Serial.print("Test time (ms): ");
  Serial.println(time2 - time1);
  
}

// Frequency Sweep
void frequencySweepStressStrain() {
  // Create arrays to hold the data
  int real[NUM_INCR + 1], imag[NUM_INCR + 1];

  // Perform the frequency sweep
  if (AD5933::frequencySweep(real, imag, NUM_INCR + 1)) {
    // Print the frequency data
    int cfreq = START_FREQ / 1000;
    for (int i = 0; i < NUM_INCR + 1; i++, cfreq += FREQ_INCR / 1000) {
      // Print raw frequency data
      // Serial.print(cfreq);
      // Serial.print(": Impedance = ");
      // Serial.print(real[i]);
      // Serial.print("/I=");
      // Serial.print(imag[i]);

      // Compute impedance
      double magnitude = sqrt(pow(real[i], 2) + pow(imag[i], 2));
      double impedance = 1 / (magnitude * gain[i]);
      // Serial.print("  |Z|=");
      //dataFile.print(", ");
      // Serial.println(impedance);
      //dataFile.print(impedance);
    }
    // Serial.println("Frequency sweep complete!");
  } else {
    Serial.println("Frequency sweep failed...");
  }
  // Post Processing -> Test first value in array (lowest frequency)
  double magnitude = sqrt(pow(real[0], 2) + pow(imag[0], 2));
  double impedance = 1 / (magnitude * gain[0]);
  
  if ((impedance < 600) && (curPad < 8)){
    stressStrain[curPad-1] = getPressure();
    // TODO 
    // Send to python that pad was contacted


    Serial.print("Pad ");
    Serial.print(curPad);
    Serial.println(" has been contacted at ");
    Serial.print(impedance);
    Serial.println(" (ohms)!");
    curPad++;
  }else{
    // TODO
    // Send to python that pad was not contacted
    Serial.print("Pad ");
    Serial.print(curPad);
    Serial.print(" has not been contacted at ");
    Serial.print(impedance);
    Serial.println(" (ohms)");
  }
}

// Mux Control Function
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

void selectPressure(float p) {
  if (p>0){
    p = p*-1;
  }
  dac.setVoltage(slope*p + yint, false);
}