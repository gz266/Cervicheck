# include <Wire.h>
# include <Adafruit_ADS1X15.h>
# include <Adafruit_MCP4725.h>
#include "AD5933.h"

Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

# define DAC_RESOLUTION (9)

const int greenLED = 5; 
const int yellowLED = 6; 
const int startbuttonPin = 7;
int startbuttonState = 0;

void setup() {
  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);
  
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);

}

void loop() {
  startbuttonState = digitalRead(startbuttonPin);
  if (startbuttonState == HIGH) {
    digitalWrite(greenLED, HIGH);
    digitalWrite(yellowLED, LOW);
    delay(100);
    digitalWrite(greenLED, LOW);
    digitalWrite(yellowLED, HIGH);
    delay(100);
  }else{
    digitalWrite(greenLED, HIGH);
    digitalWrite(yellowLED, LOW);
    delay(300);
    digitalWrite(greenLED, LOW);
    digitalWrite(yellowLED, HIGH);
    delay(300);
  }

}
