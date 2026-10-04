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
const int REF_RES_0 = 330;
const int REF_RES_1 = 3300;
const int REF_RES_2 = 5600;
const int REF_RES_3 = 10000;
const int REF_RES_4 = 15000;
const int REF_RES_5 = 18000;
const int REF_RES_6 = 22000;
const int REF_RES_7 = 27000;
int channel = 0;

char userInput;
String data;

double gain_low[20];
double gain_high[20];
double gain[20];
double impedance_arr[10];
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
    if(userInput == 'a'){
      autoSweep();
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
  

  // Perform calibration sweep
  if (!AD5933::calibrate(gain, phaseRef, reference, num_incr + 1)) {
    Serial.println("Re-Calibration failed...");
    while (true)
      ;
  }
  // for(int i = 0; i < 20; i) {
  //   Serial.print("Gain: ");
  //   Serial.println(gain[i]);
  // }
}
// void calibrateAD5933TwoPoint(int start_freq, int freq_incr, int num_incr, int reference) {
  
//   if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(start_freq - 5000) && AD5933::setIncrementFrequency(freq_incr) && AD5933::setNumberIncrements(num_incr) && AD5933::setPGAGain(PGA_GAIN_X1))) {
//     Serial.println("FAILED in initialization!");
//     while (true)
//       ;
//   }
  

//   // Perform calibration sweep
//   if (!AD5933::calibrate(gain_low, phaseRef, reference, num_incr + 1)) {
//     Serial.println("Re-Calibration failed...");
//     while (true)
//       ;
//   }
//   if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(start_freq + 5000) && AD5933::setIncrementFrequency(freq_incr) && AD5933::setNumberIncrements(num_incr) && AD5933::setPGAGain(PGA_GAIN_X1))) {
//     Serial.println("FAILED in initialization!");
//     while (true)
//       ;
//   }
//   // Perform calibration sweep
//   if (!AD5933::calibrate(gain_high, phaseRef, reference, num_incr + 1)) {
//     Serial.println("Re-Calibration failed...");
//     while (true)
//       ;
//   }
//   Serial.println("Re-Initialized!");
//   Serial.println("Re-Calibrated!");

//   for(int i=0; i < 20; i++){
//     Serial.print("Gain low: ");
//     Serial.println(gain_low[i]);
//     Serial.print("Gain high: ");
//     Serial.println(gain_high[i]);
//     gain[i] = 0.5 * (gain_low[i] + gain_high[i]);
//   }
//   Serial.println("Done");
// }

// Mux Control Function
void selectPad(int p) {
  // Pad 0 is calibration resistor, Pad 1-7 are on flex pcb
  digitalWrite(sL[0], MUXtable[p][0]);
  digitalWrite(sL[1], MUXtable[p][1]);
  digitalWrite(sL[2], MUXtable[p][2]);
  digitalWrite(sL[3], MUXtable[p][3]);
}

// Impedance algorithm
void autoSweep(){
    selectPad(11);
    calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_3);
    Serial.println("Performing impedance sweep...");
    selectPad(0);
    frequencySweepEasy();
    if(impedance_arr[2] < 8500){
      selectPad(9);
      calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_1);
      selectPad(0);
      frequencySweepEasy();
      if(impedance_arr[2] < 1200){
        selectPad(0);
        calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_0);
        selectPad(0);
        frequencySweepEasy();
        Serial.println("Final impedance values: ");
        for(int i = 0; i < 10; i++){
          Serial.println(impedance_arr[i]);
        }
        
      }
      else if(impedance_arr[2] > 4700){
        selectPad(10);
        calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_2);
        selectPad(0);
        frequencySweepEasy();
        Serial.println("Final impedance values: ");
        for(int i = 0; i < 10; i++){
          Serial.println(impedance_arr[i]);
        }
      }
      else{
        Serial.println("Final impedance values: ");
        for(int i = 0; i < 10; i++){
          Serial.println(impedance_arr[i]);
        }
      }
    }
    else if(impedance_arr[1] > 12500){
      selectPad(13);
      calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_5);
      selectPad(0);
      frequencySweepEasy();
      if(impedance_arr[1] < 16700){
        selectPad(12);
        calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_4);
        selectPad(0);
        frequencySweepEasy();
        Serial.println("Final impedance values: ");
        for(int i = 0; i < 10; i++){
          Serial.println(impedance_arr[i]);
        }
      }
      else if(impedance_arr[1] > 20500){
        selectPad(14);
        calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_6);
        selectPad(0);
        frequencySweepEasy();
        if(impedance_arr[1] > 24500){
          selectPad(15);
          calibrateAD5933(start_freq, freq_incr, num_incr, REF_RES_7);
          selectPad(0);
          frequencySweepEasy();
          Serial.println("Final impedance values: ");
          for(int i = 0; i < 10; i++){
            Serial.println(impedance_arr[i]);
          }
        }
        else{
          Serial.println("Final impedance values: ");
          for(int i = 0; i < 10; i++){
            Serial.println(impedance_arr[i]);
          }
        }
      }
      else{
        Serial.println("Final impedance values: ");
        for(int i = 0; i < 10; i++){
          Serial.println(impedance_arr[i]);
        }
      }
    }
    else{
      Serial.println("Final impedance values: ");
      for(int i = 0; i < 10; i++){
        Serial.println(impedance_arr[i]);
      }
    }
    Serial.println("Done!");
      
//   if(userInput == 'c'){
//     data = Serial.readStringUntil('\r');
//     channel = data.toInt();
//     Serial.print("Setting Channel");
//     Serial.println(channel);
//     selectPad(channel);
//   }
}