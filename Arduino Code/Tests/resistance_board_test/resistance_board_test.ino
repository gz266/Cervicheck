#include <Wire.h>
#include <Adafruit_ADS1X15.h>
Adafruit_ADS1015 ads1015;

int sL[3] = { 8, 9, 10 };
int MUXtable[8][3] = { { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 0, 1, 1 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 0 },  { 1, 1, 1 } };

void setup() {
  Serial.begin(9600);
  Wire.begin();

  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize ADC
  // ADC range is +/- 6.144 V (1 bit = 3 mV)
  ads1015.begin(0x48);

  // Initialize MUX
  for (int i = 0; i < 3; i++) {
    pinMode(sL[i], OUTPUT);
  }
}

void loop() {
  calibCheck();
  delay(500);
}

void selectPad(int p) {
  // Pad 0 is calibration resistor, Pad 1-7 are on flex pcb
  digitalWrite(sL[0], MUXtable[p][0]);
  digitalWrite(sL[1], MUXtable[p][1]);
  digitalWrite(sL[2], MUXtable[p][2]);
}

void calibCheck() {
  for(int k = 0; k < 8; k++) {
    selectPad(k);
    delay(50);
    int val = ads1015.readADC_SingleEnded(3);
    float voltage = 3.0 * val / 1000;
    Serial.print("CALIBCHECK,Pad ");
    Serial.print(k);
    Serial.print(" Voltage: ");
    Serial.println(voltage);
  }
  Serial.println("DONE");
}

void readResistance(void) {
  int val = ads1015.readADC_SingleEnded(3);
  float voltage = val * 3.0 / 1000.0;
  Serial.print("Voltage: ");
  Serial.println(voltage);
}