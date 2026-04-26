/*
impedance-rfb-sweep-test
  sweeps RFB and calibration resistors on digipots to test 
  ad5933 accuracy
*/

#include <Wire.h>
#include "AD5272.h"
#include "AD5933.h"

AD5272 rfb_pot(0x2F);
AD5272 cal_pot(0x2C);

#define START_FREQ (15000)
#define FREQ_INCR (5000)
#define NUM_INCR (1)

char userInput;
String data;
const int MAX_RES = 50000;
const int RESOLUTION = 1024;

void setup() {
  // Begin I2C
  Wire.begin();

  // Begin serial at 9600 baud for output
  Serial.begin(9600);

  // Perform initial configuration. Fail if any one of these fail.
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(START_FREQ) && AD5933::setIncrementFrequency(FREQ_INCR) && AD5933::setNumberIncrements(NUM_INCR) && AD5933::setPGAGain(PGA_GAIN_X1))) {
    Serial.println("FAILED in initialization!");
    while (true)
      ;
  }

  // Perform calibration sweep
  if (!AD5933::calibrate(gain, phase, REF_RESIST, NUM_INCR + 1)) {
    Serial.println("Calibration failed...");
    while (true)
      ;
  }
  Serial.println("Calibrated!");

  int init = rfb_pot.init() || cal_pot.init();

  if (init != 0){
    Serial.println(init);
    Serial.println("Cannot send data to the IC.");
  } else {
    Serial.println("Let's Rock & Roll");
  }
  uint16_t val = 7;
  int ret = rfb_pot.write_data(AD5272_RDAC_WRITE, val);
  if(ret != 0)  // check if data is sent successfully
    Serial.println("Error!");
  int ret = cal_pot.write_data(AD5272_RDAC_WRITE, val);
  if(ret != 0)  // check if data is sent successfully
    Serial.println("Error!");
}

void loop() {
  userInput = Serial.read();
  if(userInput == 's') {
    runTest();
  }
}

void setRFB(int res) {
  int val = res / MAX_RES * RESOLUTION
  rfb_pot.write_data(AD5272_RDAC_WRITE, val);
}

void setCal(int res) {
  int val = res / MAX_RES * RESOLUTION
  cal_pot.write_data(AD5272_RDAC_WRITE, val);
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

double frequencySweepEasy() {
  // Create arrays to hold the data
  int real[num_incr + 1], imag[num_incr + 1];
  int impedance_arr[NUM_INCR + 1];

  // Perform the frequency sweep
  if (AD5933::frequencySweep(real, imag, num_incr + 1)) {
    // Print the frequency data
    int cfreq = start_freq / 1000;
    for (int i = 0; i < num_incr + 1; i++, cfreq += freq_incr / 1000) {
      // Print raw frequency data
      // Serial.print(cfreq);
      // Serial.print(": Impedance = ");
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
      impedance_arr[i] = impedance;
    }
    int sum = 0;
    for(int i = 0; i < NUM_INCR + 1; i++) {
      sum += impedance[i];
    }
    return sum / (NUM_INCR + 1);
    // Serial.println("Frequency sweep complete!");
  } else {
    Serial.println("Frequency sweep failed...");
  }
}

void runTest() {
  int min_test;
  int max_test;
  double impedance;
  for(int rfb = 0; rfb < 30001; rfb += 500) {
    setRFB(rfb);
    for(int cal = 0; cal < 30001; cal += 500) {
      setCal(cal);
      calibrateAD5933(START_FREQ, FREQ_INCR, NUM_INCR, cal);
      if(cal < 2000) {
        min_test = 0;
        max_test = cal + 2000;
      }
      else if(cal > 28000) {
        min_test = cal - 2000;
        max_test = 30000;
      }
      else {
        min_test = cal - 2000;
        max_test = cal + 2000;
      }
      for(int test = min_test; test <= max_test; test += 250) {
        setCal(test);
        impedance = frequencySweepEasy();
        data = String(rfb) + ", " + String(cal) + ", " + String(test) + ", " + String(impedance);
        Serial.println(data);
      }
    }
  }
}