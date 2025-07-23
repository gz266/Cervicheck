String data; 

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); // Start serial communication at 9600 baud rate

}

void loop() {
  // put your main code here, to run repeatedly:
  while(Serial.available() == 0){

  }
  data = Serial.readStringUntil('\r');

}
