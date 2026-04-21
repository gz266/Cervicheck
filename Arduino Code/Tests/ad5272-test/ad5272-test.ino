#include <Wire.h>
#include "AD5272.h"

AD5272 digital_pot(0x2F);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  delay(100);
  
  // Serial.println("Scanning I2C bus...");
  // for(uint8_t addr = 0x01; addr < 0x7F; addr++) {
  //   Wire.beginTransmission(addr);
  //   if(Wire.endTransmission() == 0) {
  //     Serial.print("Device found at 0x");
  //     Serial.println(addr, HEX);
  //   }
  // }
  // Serial.println("Scan complete.");

  int init = digital_pot.init();

  if (init != 0){
    Serial.println(init);
    Serial.println("Cannot send data to the IC.");
  } else {
    Serial.println("Let's Rock & Roll");
  }

  // set new value to RDAC (0~1024)
  uint16_t data = 7;
  int ret = digital_pot.write_data(AD5272_RDAC_WRITE, data);
  if(ret != 0)  // check if data is sent successfully
    Serial.println("Error!");
}

void loop() {
  // put your main code here, to run repeatedly:
  // read the new RDAC value
  // int ret = digital_pot.read_rdac();
  // Serial.print("RDAC Value: ");
  // Serial.println(ret, DEC);
}
