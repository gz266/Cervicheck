# include <Wire.h>
# include <Adafruit_ADS1X15.h>
# include <Adafruit_MCP4725.h>

Adafruit_ADS1015 ads1015;
Adafruit_MCP4725 dac;

# define DAC_RESOLUTION (9)

void setup(void)
{
  Serial.begin(9600);
  
  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize ADC 
  // ADC range is +/- 6.144 V (1 bit = 3 mV)
  ads1015.begin(0x48);

  // Initialize DAC
  dac.begin(0x60);

  dac.setVoltage((1*4095)/5, false);
}

void loop(void)
{
  Serial.println(getPressure());
}

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
  return ((ads1015.readADC_SingleEnded(2)*3)/1000);
  //return (((ads1015.readADC_SingleEnded(0) * 3.0) / 1000) - (0.92 * 5)) / (0.018 * 5);
}