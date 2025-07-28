/*
ad5933-test
    Reads impedance values from the AD5933 over I2C and prints them serially.
    Also tests the 

// Also tests MUXes
*/

#include <Wire.h>
#include "AD5933.h"

#define START_FREQ (100000)
#define FREQ_INCR (5000)
#define NUM_INCR (5)
#define REF_RESIST (2700)

double gain[NUM_INCR + 1];
int phase[NUM_INCR + 1];

int i;
int sL[3] = { 8, 9, 10 };
//int MUXtable[8][3] = { { 1, 0, 1 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 1, 0 }, { 1, 1, 1 } };
int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 0 }, { 0, 0, 0 }, { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 }, { 0, 1, 1 }, { 1, 1, 1 } };

const int yellowLED = 7;
const int greenLED = 6;
const int startbuttonPin = 5;
int startbuttonState = 0;

void setup(void) {
  // Begin I2C
  Wire.begin();

  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  pinMode(startbuttonPin, INPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);

  // Begin serial at 9600 baud for output
  Serial.begin(9600);
  Serial.println("AD5933 Test Started!");

  // Initialize MUX
  for (i = 0; i < 3; i++) {
    pinMode(sL[i], OUTPUT);
  }


  // Perform initial configuration. Fail if any one of these fail.
  if (!(AD5933::reset() && AD5933::setInternalClock(true) && AD5933::setStartFrequency(START_FREQ) && AD5933::setIncrementFrequency(FREQ_INCR) && AD5933::setNumberIncrements(NUM_INCR) && AD5933::setPGAGain(PGA_GAIN_X1))) {
    Serial.println("FAILED in initialization!");
    while (true)
      ;
  }

  Serial.println("Initialized!");

  // Select 300 OHM resistor
  digitalWrite(sL[0], MUXtable[0][0]);
  digitalWrite(sL[1], MUXtable[0][1]);
  digitalWrite(sL[2], MUXtable[0][2]);
  
  // Perform calibration sweep
  if (!AD5933::calibrate(gain, phase, REF_RESIST, NUM_INCR + 1)) {
    Serial.println("Calibration failed...");
    while (true)
      ;
  }
  Serial.println("Calibrated!");
  
}

void loop(void) {
  runTest();
  delay(2000);
  // Lights for Ready to Test
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, HIGH);
  startbuttonState = digitalRead(startbuttonPin);
  if (startbuttonState == HIGH) {
    // Lights for Testing
    digitalWrite(yellowLED, LOW);
    digitalWrite(greenLED, HIGH);
    runTest();
  }
}

void runTest() {
  // Select 300 ohm resister
  /*
  digitalWrite(sL[0], MUXtable[0][0]);
  digitalWrite(sL[1], MUXtable[0][1]);
  digitalWrite(sL[2], MUXtable[0][2]);

  int time1 = millis();
  frequencySweepEasy();
  int time2 = millis();
  Serial.println(time2 - time1);
  */

  // Select Pad 0
  digitalWrite(sL[0], MUXtable[0][0]);
  digitalWrite(sL[1], MUXtable[0][1]);
  digitalWrite(sL[2], MUXtable[0][2]);
  frequencySweepEasy();
  delay(1000);
  /*
  int time1 = millis();
  frequencySweepEasy();
  int time2 = millis();
  Serial.println(time2 - time1);

  // Select Pad 6
  digitalWrite(sL[0], MUXtable[6][0]);
  digitalWrite(sL[1], MUXtable[6][1]);
  digitalWrite(sL[2], MUXtable[6][2]);

  time1 = millis();
  frequencySweepEasy();
  time2 = millis();
  Serial.println(time2 - time1);

  /* Time frequency Sweeps
  int mytime1;
  int mytime2;
  // Easy to use method for frequency sweep

  //frequencySweepEasy();
  for (int i = 1; i <= 10; i++) {
    mytime1 = millis();
    frequencySweepRaw();
    mytime2 = millis();
    Serial.print(mytime2 - mytime1);
    Serial.print(" ");
  }
  */
}

// Easy way to do a frequency sweep. Does an entire frequency sweep at once and
// stores the data into arrays for processing afterwards. This is easy-to-use,
// but doesn't allow you to process data in real time.
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
      Serial.println(impedance);
    }
    Serial.println("Frequency sweep complete!");
  } else {
    Serial.println("Frequency sweep failed...");
  }
}

// Removes the frequencySweep abstraction from above. This saves memory and
// allows for data to be processed in real time. However, it's more complex.
void frequencySweepRaw() {
  // Create variables to hold the impedance data and track frequency
  int real, imag, i = 0, cfreq = START_FREQ / 1000;

  // Initialize the frequency sweep
  if (!(AD5933::setPowerMode(POWER_STANDBY) &&           // place in standby
        AD5933::setControlMode(CTRL_INIT_START_FREQ) &&  // init start freq
        AD5933::setControlMode(CTRL_START_FREQ_SWEEP)))  // begin frequency sweep
  {
    Serial.println("Could not initialize frequency sweep...");
  }

  // Perform the actual sweep
  while ((AD5933::readStatusRegister() & STATUS_SWEEP_DONE) != STATUS_SWEEP_DONE) {
    // Get the frequency data for this frequency point
    if (!AD5933::getComplexData(&real, &imag)) {
      Serial.println("Could not get raw frequency data...");
    }

    // Print out the frequency data
    //Serial.print(cfreq);
    //Serial.print(": R=");
    //Serial.print(real);
    //Serial.print("/I=");
    //Serial.print(imag);

    // Compute impedance
    double magnitude = sqrt(pow(real, 2) + pow(imag, 2));
    double impedance = 1 / (magnitude * gain[i]);
    //Serial.print("  |Z|=");
    //Serial.println(impedance);

    // Increment the frequency
    i++;
    cfreq += FREQ_INCR / 1000;
    AD5933::setControlMode(CTRL_INCREMENT_FREQ);
  }

  //Serial.println("Frequency sweep complete!");

  // Set AD5933 power mode to standby when finished
  if (!AD5933::setPowerMode(POWER_STANDBY))
    Serial.println("Could not set to standby...");
}

/*
bool diagnosticSweep() {
  // Create variables to hold the impedance data and track frequency
  int real, imag, i = 0, cfreq = START_FREQ / 1000;

  // Initialize the frequency sweep
  if (!(AD5933::setPowerMode(POWER_STANDBY) &&           // place in standby
        AD5933::setControlMode(CTRL_INIT_START_FREQ) &&  // init start freq
        AD5933::setControlMode(CTRL_START_FREQ_SWEEP)))  // begin frequency sweep
  {
    Serial.println("Could not initialize frequency sweep...");
  }

  // Perform the diagnostic sweep to determine if contact has been made
  // Assume imepedance values of 15000 ohms mean that air is being contacted.
  // Assume that half of the values in a sweep must be less than 15000 for a test to be considered tissue contact
  int no_contact = NUM_INCR / 2;
  int contact = 0;
  while (((AD5933::readStatusRegister() & STATUS_SWEEP_DONE) != STATUS_SWEEP_DONE)) {
    // Get the frequency data for this frequency point
    if (contact < no_contact) {
      return false;
      if (!AD5933::setPowerMode(POWER_STANDBY))
        Serial.println("Could not set to standby...");
    }
    if (!AD5933::getComplexData(&real, &imag)) {
      Serial.println("Could not get raw frequency data...");
    }

    // Print out the frequency data
    // Serial.print(cfreq);
    // Serial.print(": R=");
    // Serial.print(real);
    // Serial.print("/I=");
    // Serial.print(imag);

    // Compute impedance
    double magnitude = sqrt(pow(real, 2) + pow(imag, 2));
    double impedance = 1 / (magnitude * gain[i]);
    // Serial.print("  |Z|=");
    // Serial.println(impedance);

    if (impedance > 15000) {
      contact++;
    }

    // Increment the frequency
    i++;
    cfreq += FREQ_INCR / 1000;
    AD5933::setControlMode(CTRL_INCREMENT_FREQ);
  }

  // Set AD5933 power mode to standby when finished
  if (!AD5933::setPowerMode(POWER_STANDBY))
    Serial.println("Could not set to standby...");

  return true;
}
*/
