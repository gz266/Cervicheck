#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP4725.h>
#include <SD.h>


Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

#define DAC_RESOLUTION (9)
char userInput;

#define REF_RESIST (300)

// Pressure Constants
// 12% gel: test -2 increment, 21 increases
// 7.5% gel: test -1 increment, 30 increases
float pres_start = -1;
float pres_incr = -1;
int pres_num_incr =  30;
float res_volt_thresh = 4.5;

int i;

int sL[3] = { 8, 9, 10 };
// First value corresponds to 300 ohm resistor
// Green: 560 vs non-Green 270
// int MUXtable[8][3] = { { 1, 1, 0 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 1 } };  // purple board
// int MUXtable[8][3] = { { 1, 0, 1 }, { 0, 1, 1 }, { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 1, 1, 0 }, { 1, 1, 1 } }; // green board
// int MUXtable[8][3] = { { 1, 0, 1 }, { 1, 1, 1 }, { 0, 1, 1 }, { 0, 0, 1 }, { 0, 1, 0 }, { 1, 0, 0 }, { 0, 0, 0 }, { 1, 1, 0 } }; // new pad arrangement
// Flipped new pad arrangement, if pads are flipped
// int MUXtable[8][3] = { { 0, 0, 0 }, { 0, 0, 1 }, { 0, 1, 0 }, { 0, 1, 1 }, { 1, 0, 0 }, { 1, 0, 1 }, { 1, 1, 0 }, { 1, 1, 1 } };
int MUXtable[8][3] = { { 1, 1, 1 }, { 1, 1, 0 }, { 1, 0, 1 }, { 1, 0, 0 }, { 0, 1, 1 }, { 0, 1, 0 }, { 0, 0, 1 }, { 0, 0, 0 } };

int curPad = 1;
float stressStrain[8] = {0,0,0,0,0,0,0,0};
// float stressStrain[7] = {0, 0, 0, 0, 0, 0, 0};

float padRes[8] = {5, 5, 5, 5, 5, 5, 5, 5};

// Board Constants
const int valve = 7;

float pressure;

// Pressure Control Constants
// y = mx where y is digital value to supply DAC and x is desired pressure (-kPa)
float slope = -79.24 ;
float yint = 44.45;
String data;

//SD Card
File dataFile;
String filename = "Data.csv";
const int chipSelectPin = 2;


void setup(void) {
  Serial.begin(9600);
  Wire.begin();

  // Valve Release
  pinMode(valve, OUTPUT);
  digitalWrite(valve, LOW);

  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize MUX
  for (i = 0; i < 3; i++) {
    pinMode(sL[i], OUTPUT);
  }

  // Select 300 OHM resistor
  selectPad(0);

  // Initialize ADC
  // ADC range is +/- 6.144 V (1 bit = 3 mV)
  ads1015.begin(0x48);

  // Initialize DAC
  dac.begin(0x60);
  // Serial.println("Get ready");
  // delay(5000);
  // calibratePressure();
  // selectPressure(0);
  // Serial.println("Test in 5 seconds");
  // delay(5000);
  // pressureSweep();
  releaseValve(0);
}
int stop = 0;
void loop(void) {

  // dac.setVoltage((0*4095)/5, false);
  // scanI2C();
  // calibCheck();
  // delay(1000);
  // selectPressure(10);
  // calibCheck();
  // delay(2000);
  if(Serial.available()>0){
    userInput = Serial.read();               // read user input
    if(userInput == 's'){         
      long t1 = millis();
      pressureSweep();
      long t2 = millis();
      Serial.println("Done!");
      for (int i = 0; i < 8; i++) {
        Serial.println(stressStrain[i]);
      }
      // for (int i = 0; i < 7; i++) {
      //   Serial.println(stressStrain[i]);
      // } 
      Serial.print("Time: ");
      Serial.println(t2-t1);
      for(int i=0; i < 8; i++){
        stressStrain[i] = 0;
      }
      // for(int i=0; i < 7; i++){
      //   stressStrain[i] = 0;
      // }
      Serial.print("Releasing Valve: ");
      releaseValve(1);
      delay(5000);
      releaseValve(0);
    }

    if(userInput == 'p'){     
        calibratePressure();
        selectPressure(0);
      }

    if(userInput == 'r'){
      data = Serial.readStringUntil('\r');
      slope = data.toFloat();
      data = Serial.readStringUntil('\r');
      yint = data.toFloat();
      }

    if(userInput == 'i'){
      data = Serial.readStringUntil('\r');
      pres_start = data.toFloat();
      data = Serial.readStringUntil('\r');
      pres_incr = data.toFloat();
      data = Serial.readStringUntil('\r');
      pres_num_incr = data.toInt();
      data = Serial.readStringUntil('\r');
      float thresh = data.toFloat();
      if (thresh > 0 && thresh <= 5.0) {
        res_volt_thresh = thresh;
      } else {
        Serial.print("Ignored out-of-range contact threshold: ");
        Serial.println(thresh);
      }
      Serial.print("Contact voltage threshold (V): ");
      Serial.println(res_volt_thresh);
    }
    if(userInput == 't'){
      data = Serial.readStringUntil('\r');
      releaseValve(data.toInt());
      }
      
    // --- TROUBLESHOOTING: check ADC/pad-0 calibration resistor baseline ---
    if(userInput == 'c'){
      calibCheck();
    }
    // --- END TROUBLESHOOTING ---
  }
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

void readAllPads(float res_arr[]) {
  for(int k = 0; k < 8; k++) {
    selectPad(k);
    delay(50);
    res_arr[k] = ads1015.readADC_SingleEnded(3) * 3.0 / 1000;
  }
}
void calibratePressure() {
  Serial.println("Voltage: ");
  Serial.println("50");
  Serial.println("250");
  Serial.println("500");
  Serial.println("750");
  Serial.println("1000");
  Serial.println("1250");
  Serial.println("Pressure: ");
  for (int i = 50; i < 251; i+=200){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
  for (int i = 500; i < 1500; i+=250){
    dac.setVoltage(i, false);
    delay(3000);
    // Serial.print(i);
    Serial.println(getPressure());
  }
  Serial.println("Done!");
}

void precondition(int cycles){
  for (int i = 0; i < cycles; i++){
    // On
    releaseValve(0);
    selectPressure(0.5);
    delay(200);
    Serial.print("Pressure Held: ");
    Serial.println(getPressure());

    // Off
    releaseValve(1);
    selectPressure(0);
    delay(500);
    Serial.print("Pressure Released: ");
    Serial.println(getPressure());
  }
  releaseValve(0);
}
// Testing Functions
void pressureSweep() {
  // curPad = 0;
  curPad = 0;
  pressure = pres_start;
  int sweep;
  precondition(10);
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

    float currentPressure = getPressure();
    Serial.print("Current Pressure (kPa): ");
    Serial.println(currentPressure);
    streamPressureSample(pressure, getPressure(), curPad);
    int count = 0;
    float error = 0.1;
    // Just in case pressure is not reached
    while (abs(getPressure()-pressure) > error){
      count++;
      if(count % 5 == 0) {
        streamPressureSample(pressure, getPressure(), curPad);
      }
      if (count > 100){
        break;
      }
    }
    streamPressureSample(pressure, getPressure(), curPad);
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

  // --- TROUBLESHOOTING: confirm mux lines are actually switching ---
  // Serial.print("MUX,");
  // Serial.print(padnum);
  // Serial.print(",");
  // Serial.print(digitalRead(sL[0]));
  // Serial.print(digitalRead(sL[1]));
  // Serial.println(digitalRead(sL[2]));
  // --- END TROUBLESHOOTING ---

  int time1 = millis();
  // frequencySweepStressStrain();
  resistanceRead();
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

void resistanceRead() {
  // int val = ads1015.readADC_SingleEnded(3);
  // float voltage = 3.0 * val / 1000;
  readAllPads(padRes);
  float voltage = 5.0;
  for(int v = curPad; v < 8; v++) {
    if(padRes[v] < res_volt_thresh) {
      voltage = padRes[v];
      curPad = v;
    }
    else
      break;
  }
  // --- TROUBLESHOOTING LOG ---
  // Serial.print("DEBUG,");
  // Serial.print(millis());
  // Serial.print(",Pad,");
  // Serial.print(curPad);
  // Serial.print(",Voltage,");
  // Serial.print(voltage);
  // Serial.print(",Pressure,");
  // Serial.println(getPressure());
  // --- END TROUBLESHOOTING LOG ---

  if ((voltage < res_volt_thresh) && (curPad < 8)){
    float contactPressure = getPressure();
    stressStrain[curPad] = contactPressure;
    // stressStrain[curPad - 1] = contactPressure;
    streamPressureSample(pressure, contactPressure, curPad);
    streamContactMarker(curPad, contactPressure, voltage);

    Serial.print("Pad ");
    Serial.print(curPad);
    Serial.print(" has been contacted at ");
    Serial.print(voltage);
    Serial.println(" (volts)!");
    curPad++;

  }else{
    Serial.print("Pad ");
    Serial.print(curPad);
    Serial.print(" has not been contacted at ");
    Serial.print(voltage);
    Serial.println(" (volts)");
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

void releaseValve(int a){
  if (a == 1){
    digitalWrite(valve, HIGH);
  }else{
    digitalWrite(valve, LOW);
  }
}

void scanI2C() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Scanning...");

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println("  !");
      nDevices++;
    } else if (error == 4) {
      Serial.print("Unknown error at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
    }
  }

  if (nDevices == 0) {
    Serial.println("No I2C devices found\n");
  } else {
    Serial.println("done\n");
  }
}

void streamPressureSample(float targetPressure, float actualPressure, int padnum) {
  Serial.print("PRESSURE,");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(targetPressure);
  Serial.print(",");
  Serial.print(actualPressure);
  Serial.print(",");
  Serial.println(padnum);
}

void streamContactMarker(int padnum, float contactPressure, double impedance) {
  Serial.print("CONTACT,");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(padnum);
  Serial.print(",");
  Serial.print(contactPressure);
  Serial.print(",");
  Serial.println(impedance);
}