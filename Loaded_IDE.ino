#include <OneWire.h>
#include <DallasTemperature.h>
#include <PID_v1.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define ONE_WIRE_BUS 2
#define SSR_PIN 8

LiquidCrystal_I2C lcd(0x27, 16, 2);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

double setPoint = 0.0;
double inputTemp = 0.0;
double pidOutput = 0.0;

double Kp = 80.0;
double Ki = 1.0;
double Kd = 0.0;

PID myPID(&inputTemp, &pidOutput, &setPoint, Kp, Ki, Kd, DIRECT);

unsigned long windowSize = 100UL;
unsigned long windowStartTime = 0;

float cookTimeMinutes = 0.0;
unsigned long cookStartMillis = 0;
bool cookingActive = false;

String serialBuffer = "";
unsigned long lastLcdUpdate = 0;
const unsigned long lcdInterval = 500UL;

void setup() {
  Serial.begin(9600);
  sensors.begin();
  lcd.init();
  lcd.backlight();
  pinMode(SSR_PIN, OUTPUT);
  digitalWrite(SSR_PIN, LOW);
  myPID.SetOutputLimits(0, (double)windowSize);
  myPID.SetSampleTime(1000);
  myPID.SetMode(AUTOMATIC);
  windowStartTime = millis();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  delay(1200);
  lcd.clear();
}

void processCommand(String data) {
  data.trim();
  if (data.length() == 0) return;
  if (data.startsWith("TEMP:") || data.startsWith("Temp:") || data.startsWith("temp:")) {
    String val = data.substring(data.indexOf(':') + 1);
    val.trim();
    double newTemp = val.toFloat();
    if (newTemp < 5.0) newTemp = 5.0;
    if (newTemp > 120.0) newTemp = 120.0;
    setPoint = newTemp;
    Serial.println("ACK:TEMP");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("SetPoint:");
    lcd.setCursor(0, 1);
    lcd.print(setPoint, 1);
    lcd.print((char)223);
    lcd.print("C");
    delay(900);
    lastLcdUpdate = millis();
  } else if (data.startsWith("TIME:") || data.startsWith("Time:") || data.startsWith("time:")) {
    String val = data.substring(data.indexOf(':') + 1);
    val.trim();
    double newTime = val.toFloat();
    if (newTime < 0.1) newTime = 0.1;
    if (newTime > 60.0) newTime = 60.0;
    cookTimeMinutes = newTime;
    cookStartMillis = millis();
    cookingActive = true;
    Serial.println("ACK:TIME");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Cook Time:");
    lcd.setCursor(0, 1);
    lcd.print(cookTimeMinutes, 1);
    lcd.print(" min");
    delay(900);
    lastLcdUpdate = millis();
  }
}

void readSerialCommands() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      processCommand(serialBuffer);
      serialBuffer = "";
    } else {
      serialBuffer += c;
      if (serialBuffer.length() > 200) serialBuffer = "";
    }
  }
}

void writeLcdStatus() {
  if (millis() - lastLcdUpdate < lcdInterval) return;
  lastLcdUpdate = millis();
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(inputTemp, 1);
  lcd.print((char)223);
  lcd.print("C ");
  lcd.print("Set:");
  if (setPoint > 0.1) {
    lcd.print(setPoint, 1);
    lcd.print((char)223);
    lcd.print("C");
  } else {
    lcd.print("-- ");
  }
  lcd.setCursor(0, 1);
  if (cookingActive) {
    float remainingMinutes = cookTimeMinutes - ((millis() - cookStartMillis) / 60000.0);
    if (remainingMinutes < 0) remainingMinutes = 0;
    double errorPercent = ((inputTemp - setPoint) / setPoint) * 100;
    lcd.print("Left:");
    lcd.print(remainingMinutes, 1);
    lcd.print("m ");
    lcd.print("Err:");
    lcd.print(errorPercent, 1);
    lcd.print("%");
  } else {
    lcd.print("Idle           ");
  }
}

void loop() {
  readSerialCommands();
  sensors.requestTemperatures();
  inputTemp = sensors.getTempCByIndex(0);
  if (inputTemp == DEVICE_DISCONNECTED_C) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sensor Error!");
    digitalWrite(SSR_PIN, LOW);
    delay(1000);
    return;
  }
  if (cookingActive) {
    float elapsedMinutes = (millis() - cookStartMillis) / 60000.0;
    if (elapsedMinutes >= cookTimeMinutes) {
      cookingActive = false;
      pidOutput = 0;
      digitalWrite(SSR_PIN, LOW);
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Cooking Done");
      Serial.println("EVENT:COOK_DONE");
      delay(1200);
      lastLcdUpdate = millis();
    }
  }
  if (!cookingActive) pidOutput = 0;
  if (cookingActive && setPoint > 0.1) {
    myPID.Compute();
    if (inputTemp >= setPoint) pidOutput = 0;
  }
  unsigned long now = millis();
  if (now - windowStartTime >= windowSize) {
    windowStartTime += windowSize * ((now - windowStartTime) / windowSize);
  }
  if (cookingActive && (now - windowStartTime) < (unsigned long)pidOutput) {
    digitalWrite(SSR_PIN, HIGH);
  } else {
    digitalWrite(SSR_PIN, LOW);
  }
  writeLcdStatus();
  delay(50);
}
