float current = 1.5;
float prev = 1.5;

void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(0));
}

void loop() {
  // simulate normal variation
  current += random(-10, 10) / 100.0;

  // simulate theft spike occasionally
  if (random(0, 10) > 7) {
    current += random(10, 20) / 10.0;
  }

  float spike = abs(current - prev);

  Serial.print(current);
  Serial.print(" ");
  Serial.println(spike);

  prev = current;
  delay(500);
}