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

char userInput;
String data;

double gain[20];
int phase[20];


void setup(void) {
  // Begin I2C
  Wire.begin();

  pinMode(A2, INPUT);

  // Begin serial at 9600 baud for output
  Serial.begin(9600);
  Serial.println("AD5933 Test Started!");
  
  // Perform initial configuration. Fail if any one of these fail.
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(start_freq) && AD5933::setIncrementFrequency(freq_incr) && AD5933::setNumberIncrements(num_incr) && AD5933::setPGAGain(PGA_GAIN_X1))) {
    Serial.println("FAILED in initialization!");
    while (true)
      ;
  }
  if (!AD5933::calibrate(gain, phase, ref_resist, num_incr + 1)) {
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
      double magnitude = sqrt(pow(real[i], 2) + pow(imag[i], 2));
      double impedance = 1 / (magnitude * gain[i]);

      // Serial.print("  |Z|=");
      Serial.println(impedance);
      
      Serial.print("R: ");
      Serial.println(real[i],10);
      Serial.print("I: ");
      Serial.println(imag[i],10);
      Serial.print("Mag: ");
      Serial.println(magnitude,10);
      Serial.print("Gain: ");
      Serial.println(gain[i],10);
      Serial.print("Phase: ");
      Serial.println(phase[i],10);


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
  if (!AD5933::calibrate(gain, phase, reference, num_incr + 1)) {
    Serial.println("Re-Calibration failed...");
    while (true)
      ;
  }
  Serial.println("Re-Calibrated!");

}
