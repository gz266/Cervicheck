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

int setpoint = -5;

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
  kd = 0.01;
  
  out = 1;
}

void loop(void)
{
  /*
  // Lights for Ready to Test
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, HIGH);
  startbuttonState = digitalRead(startbuttonPin);
  if (startbuttonState == HIGH){
    // Lights for Testing
    digitalWrite(yellowLED, LOW);
    digitalWrite(greenLED, HIGH);
  }
  */
  double now = millis();
  dt = (now - lasttime)/1000.0;
  lasttime = now;

  double actual = getPressure();
  double error = setpoint-actual;
  out = PID(error);
  // 4 Parameters: starting voltage as well
  // Ensures that PID control doesn't begin until contact is made (when pressure goes below -1 based on testing)
  // Currently, the starting voltage is arbitrarily set to 1 (how to determine?)
  if (actual > -1){
    integral = 0;
    out = 1;
  }

  dac.setVoltage((out*4095)/5, false);

  // Serial.print("Out (V) ");
  Serial.print(out);
  Serial.print(", ");
  // Serial.print("Actual (kPa )");
  Serial.print(actual);

  Serial.print(", ");
  // Serial.print("Setpoint");
  Serial.println(setpoint);

}

double PID(double error)
{
  /*
    Controls the activity of the pressure transducer by setting the output voltage of the DAC
    Utilizes PID control with the Ziegler-Nichols method (no overshoot) to tune

    Accurate to +- 0.1 kPa

    Paramters: vin, voltage supplied to pressure transducer
    Returns: new voltage to be supplied to the vacuum regulator
  */

  double proportional = error;
  integral += error * dt;
  derivative = (error-previous) / dt;
  previous = error;
  double output = -((kp*proportional) + (ki*integral) + (kd * derivative));
  
  if (output < 0) {return 0;}
  if (output > 5) {return 5;}
  return output;
}

int calibratePID(){

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