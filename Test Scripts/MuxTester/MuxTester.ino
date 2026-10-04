# include <Wire.h>
# include <Adafruit_ADS1X15.h>
# include <Adafruit_MCP4725.h>
# include <SD.h>

# include "AD5933.h"
# include <SPI.h>

Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

// Constants for AD5933
# define START_FREQ (10000)
# define FREQ_INCR (5000)
# define NUM_INCR (4)  //was 18, changing to 10 for demo
# define REF_RESIST (300)

// DAC
#define DAC_RESOLUTION (9)
double gain[NUM_INCR + 1];
int phase[NUM_INCR + 1];

// MUX Setup
int Signal = 5;
int i;
int sL[3] = {8, 9, 10};

int MUXtable[8][3] = { { 1, 0, 1 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 1, 0 }, { 1, 1, 1 } };
int pressure_readings[5] = {-5, -10, -15, -20, -25};

const int E = 3;
const int S0 = 5;
const int S1 = 6;
const int S2 = 7;
const int Z = 4;

void setup(void) {
  Serial.begin(9600);
  Wire.begin();

  // Initialize Pins

  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  Serial.println("MUX Test Started!");

  pinMode(Z, OUTPUT);
  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(E, OUTPUT);

  digitalWrite(Z, HIGH);
  digitalWrite(S0, HIGH);
  digitalWrite(S1, HIGH);
  digitalWrite(S2, LOW);
  digitalWrite(E, LOW);


}

void loop(void) {
  /*
  Serial.println("Switch to High");
  digitalWrite(sL[0], 1);
  digitalWrite(sL[1], 1);
  digitalWrite(sL[2], 1);

  delay(3000);
  
  Serial.println("Switch to low");
  digitalWrite(sL[0], 0);
  digitalWrite(sL[1], 0);
  digitalWrite(sL[2], 0);

  delay(3000);
  */
}


