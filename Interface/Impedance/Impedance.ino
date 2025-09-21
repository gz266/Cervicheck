/*
ad5933-test
    Reads impedance values from the AD5933 over I2C and prints them serially.
*/

#include <Wire.h>
#include "AD5933.h"

int start_freq = 10000;
int freq_incr = 5000;
int num_incr = 5;
int ref_resist = 270;
int channel = 0;

char userInput;
String data;

double gain[20];
double phase[20];
double phaseRef[20];

int sL[4] = {7, 6, 5, 4};

int MUXtable[16][4] = { { 0, 0, 0, 0 }, { 1, 0, 0, 0 }, { 0, 1, 0, 0 }, { 1, 1, 0, 0 }, { 0, 0, 1, 0 }, { 1, 0, 1, 0 }, { 0, 1, 1, 0 }, { 1, 1, 1, 0 }, { 0, 0, 0, 1 }, { 1, 0, 0, 1}, { 0, 1, 0, 1 }, { 1, 1, 0, 1 }, { 0, 0, 1, 1 }, { 1, 0, 1, 1}, { 0, 1, 1, 1 }, { 1, 1, 1, 1 }};


void setup(void) {
  // Begin I2C
  Wire.begin();

  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  
  // Begin serial at 9600 baud for output
  Serial.begin(9600);
  Serial.println("AD5933 Test Started!");
  
  // Perform initial configuration. Fail if any one of these fail.
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(start_freq) && AD5933::setIncrementFrequency(freq_incr) && AD5933::setNumberIncrements(num_incr) && AD5933::setPGAGain(PGA_GAIN_X1))) {
    Serial.println("FAILED in initialization!");
    while (true)
      ;
  }
  if (!AD5933::calibrate(gain, phaseRef, ref_resist, num_incr + 1)) {
    Serial.println("Calibration failed...");
    while (true);
  }
  Serial.println("Calibrated!");
  
}

void loop(void) {
  if(Serial.available()>0){
    userInput = Serial.read();   
    if(userInput == 'o'){
      data = Serial.readStringUntil('\r');
      start_freq = data.toInt();
      data = Serial.readStringUntil('\r');
      freq_incr = data.toInt();
      data = Serial.readStringUntil('\r');
      num_incr = data.toInt();
      data = Serial.readStringUntil('\r');
      ref_resist = data.toInt();
      calibrateAD5933(start_freq, freq_incr, num_incr, ref_resist);
    }
    if(userInput == 'p'){
      Serial.println("Performing impedance sweep...");
      frequencySweepEasy();
    }
    if(userInput == 'c'){
      data = Serial.readStringUntil('\r');
      channel = data.toInt();
      Serial.print("Setting Channel");
      Serial.println(channel);
      selectPad(channel);
    }
  }

}

// Easy way to do a frequency sweep. Does an entire frequency sweep at once and
// stores the data into arrays for processing afterwards. This is easy-to-use,
// but doesn't allow you to process data in real time.
void frequencySweepEasy() {
  // Create arrays to hold the data
  int real[num_incr + 1], imag[num_incr + 1];

  // Perform the frequency sweep
  if (AD5933::frequencySweep(real, imag, num_incr + 1)) {
    // Print the frequency data
    int cfreq = start_freq / 1000;
    for (int i = 0; i < num_incr + 1; i++, cfreq += freq_incr / 1000) {
      // Print raw frequency data
      Serial.print(cfreq);
      Serial.print(": Impedance = ");
      // Serial.print(real[i]);
      // Serial.print("/I=");
      // Serial.print(imag[i]);

      // Compute impedance
      // phase[i] phase from the board
      double phase_new = (int)(atan2(imag[i], real[i]) * (180.0 / M_PI)); // Convert to degrees
      
      double magnitude = sqrt(pow(real[i], 2) + pow(imag[i], 2));
      double impedance = 1 / (magnitude * gain[i]);
      phase[i] = atan2(imag[i], real[i]) * (180.0 / M_PI) - phaseRef[i]; // Convert to degrees


      // Serial.print("  |Z|=");
      Serial.println(impedance);

    }
    Serial.println("Frequency sweep complete!");
  } else {
    Serial.println("Frequency sweep failed...");
  }
}

void calibrateAD5933(int start_freq, int freq_incr, int num_incr, int reference) {
  
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(start_freq) && AD5933::setIncrementFrequency(freq_incr) && AD5933::setNumberIncrements(num_incr) && AD5933::setPGAGain(PGA_GAIN_X1))) {
    Serial.println("FAILED in initialization!");
    while (true)
      ;
  }
  Serial.println("Re-Initialized!");

  // Perform calibration sweep
  if (!AD5933::calibrate(gain, phaseRef, reference, num_incr + 1)) {
    Serial.println("Re-Calibration failed...");
    while (true)
      ;
  }
  Serial.println("Re-Calibrated!");

}

// Mux Control Function
void selectPad(int p) {
  // Pad 0 is calibration resistor, Pad 1-7 are on flex pcb
  digitalWrite(sL[0], MUXtable[p][0]);
  digitalWrite(sL[1], MUXtable[p][1]);
  digitalWrite(sL[2], MUXtable[p][2]);
  digitalWrite(sL[3], MUXtable[p][3]);
}
