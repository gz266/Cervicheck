# include <Wire.h>
# include <Adafruit_ADS1X15.h>
# include <Adafruit_MCP4725.h>

Adafruit_MCP4725 dac;
Adafruit_ADS1015 ads1015;

# define DAC_RESOLUTION (9)

const int yellowLED = 5;
const int greenLED = 6;
const int startbuttonPin = 7;
int startbuttonState = 0;

int mytime1;
int mytime2;

double dt;
double integral, derivative = 0;
double previous, out, lasttime = 0;
double kp, ki, kd;

bool was_holding = false;
double cur = 0;

void setup(void)
{
  Serial.begin(9600);

  // LEDs
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  
  // Pull pin A2 to ground
  pinMode(A2, OUTPUT);
  digitalWrite(A2, LOW);

  // Initialize ADC 
  // ADC range is +/- 6.144 V (1 bit = 3 mV)
  ads1015.begin(0x48);

  // Initialize DAC
  dac.begin(0x60);

  // Recalibrate DAC, use x instead of 4095 for exact voltage values
  // Start with no vacuum pressure, use PID control to find initial value
  //dac.setVoltage((5*4095)/5, false);
  

  kp = 0.5;
  ki = 0.2;
  kd = 0.05;
  
  out = 1;
}

void loop(void)
{
  double now = millis();
  dt = (now - lasttime)/1000.0;
  lasttime = now;

  controlPressure();

  Serial.print("L:");
  Serial.print(0);
  Serial.print(", ");

  Serial.print("H:");
  Serial.print(-10);
  Serial.print(", ");

  Serial.print("Holding Pressure:");
  Serial.print(cur);
  Serial.print(", ");
  
  Serial.print("Current Pressure:");
  Serial.println(getPressure());
}

void controlPressure()
{
  /* 
  was_holding/cur logic: When the button is pressed, the first moment it is pressed contains the pressure
  value that should be held, similar to what would occur when a test is run.
  This value must be saved by the system, hence the logic system which tracks if the system has been holding.
  If the system hasn't been holding, then the button must have been recently pressed and the pressure value is saved.
  */
  startbuttonState = digitalRead(startbuttonPin);
  if (startbuttonState == HIGH){
    // Hold Pressure
    if (!was_holding) {
      cur = getPressure();
      was_holding = true;
    }
    PID(cur);
  }else{
    // Increase Pressure
    PID(getPressure()-1);
    was_holding = false;
  }
}

double PID(double setpoint)
{
  /*
    Controls the activity of the pressure transducer by setting the output voltage of the DAC

    Paramters: vin, voltage supplied to pressure transducer
    Returns: new voltage to be supplied to the vacuum regulator
  */
  double actual = getPressure();
  double error = setpoint-actual;
  // Calculate kp, ki values (Calibrate, fit to curve, place function here)

  integral += error * dt;
  derivative = (error-previous) / dt;
  previous = error;
  double output = -((kp*error) + (ki*integral) + (kd * derivative));
  
  if (output < 0) {output = 0;}
  if (output > 5) {output = 5;}
  if (actual > -1){
    integral = 0;
    derivative = 0;
    output = 1;
  }
  
  dac.setVoltage((output*4095)/5, false);
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

  return (((ads1015.readADC_SingleEnded(0) * 3.0) / 1000) - (0.92 * 5)) / (0.018 * 5);
}