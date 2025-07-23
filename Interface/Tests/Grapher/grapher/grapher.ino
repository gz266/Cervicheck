# include <Wire.h>
# include <Adafruit_ADS1X15.h>
# include <Adafruit_MCP4725.h>

Adafruit_ADS1015 ads1015;
Adafruit_MCP4725 dac;

# define DAC_RESOLUTION (9)
// int analogPin = 3;     
int data = 0;           
char userInput;

void setup(){
  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  Serial.begin(9600);
  // Serial.println("MCP4725A1 Test");
  dac.begin(0x60);                     //  setup serial
  ads1015.begin(0x48);
  dac.setVoltage((2*4095)/5, false);
}

void loop(){
  // Serial.println(getPressure());
  if(Serial.available()> 0){ 
      
      userInput = Serial.read();               // read user input
        
        if(userInput == 'g'){                  // if we get expected value 

              data = getPressure();    // read the input pin
              Serial.println(data);            
              
        } // if user input 'g' 
    } // Serial.available
} // Void Loop

float getPressure(void)
{
  /*
    Returns pressure from the MPXV5050VC6T1 pressure sensor

    Paramters: None
    Returns: takes in voltage reading from sensor from the ADS1015 pressure sensor and returns kPa

    With testing from timing, function takes 2 milliseconds to run
  */

  // int16_t adc0; float vout; float pressure;
  // adc0 = ads1015.readADC_SingleEnded(0);         // output in bits, from A0
  // vout = ((adc0 * 3.0) / 1000);    // Convert bits to voltage, found on ADS1015 data sheet
  // pressure = (vout-(0.92*5))/(0.018*5);    // Convert voltage to pressure, found on MPXV5050VC6T1 data sheet
  float vout = ads1015.readADC_SingleEnded(2);
  return (((ads1015.readADC_SingleEnded(0) * 3.0) / 1000) - (0.92 * ((vout * 3.0) / 1000))) / (0.018 * ((vout * 3.0) / 1000));
  // return ((ads1015.readADC_SingleEnded(2) * 3.0) / 1000);
  // return (((ads1015.readADC_SingleEnded(2) * 3.0) / 1000) - (0.92 * 5)) / (0.018 * 5);
}