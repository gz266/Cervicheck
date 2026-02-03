#include <Wire.h>
#include <Adafruit_MCP4725.h>
Adafruit_MCP4725 dac;
#define DAC_RESOLUTION (9)

void setup(){
  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  Serial.begin(9600);
  Serial.println("MCP4725A1 Test");
  dac.begin(0x60);

}

void loop(void){
  // put your main code here, to run repeatedly:
  dac.setVoltage((1*4095)/5, false);
  delay(500);
  dac.setVoltage((2*4095)/5, false);
  delay(500);
  dac.setVoltage((3*4095)/5, false);
  delay(500);
}
