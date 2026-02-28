//Libraries: Adafruit BNO08x, Adafruit BusIO
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type"
#include <Adafruit_BNO08x.h>
#pragma clang diagnostic pop
#include <Wire.h>
#include <math.h>
#include <string.h>

#define BNO08X_RESET -1   // no reset pin for I2C
#define REPORT_INTERVAL_US 20000  // change to 10000 if you want 100 Hz data (lower value means faster data)
#define QUAT_RAD_TO_DEG (57.2957795f)

Adafruit_BNO08x bno08x(BNO08X_RESET);
sh2_SensorValue_t sensorValue;

static void printPadded(float val, int width);

void setup(void) {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {
    delay(10);
  }

  Wire.begin();
  Wire.setClock(100000);  // 100 kHz, more reliable on long/breadboard wires

  if (!bno08x.begin_I2C()) {
    Serial.println("Failed to find BNO08x chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("BNO08x Found!");

  if (!bno08x.enableReport(SH2_GAME_ROTATION_VECTOR, REPORT_INTERVAL_US)) {
    Serial.println("Could not enable rotation vector"); //runs when the sensor is not found
    while (1) {
      delay(10);
    }
  }

  Serial.println("Reading orientation (Ctrl+C to stop)...");
  Serial.println("      Roll      Pitch        Yaw");
  Serial.println("----------------------------------");
}

void loop(void) {
  if (bno08x.wasReset()) {
    bno08x.enableReport(SH2_GAME_ROTATION_VECTOR, REPORT_INTERVAL_US); 
  }

  if (!bno08x.getSensorEvent(&sensorValue)) {
    delay(1);  // avoid busy-loop when sensor has no new data
    return;
  }

  if (sensorValue.sensorId != SH2_GAME_ROTATION_VECTOR) {
    return;
  }

  float i    = sensorValue.un.gameRotationVector.i;
  float j    = sensorValue.un.gameRotationVector.j;
  float k    = sensorValue.un.gameRotationVector.k;
  float real = sensorValue.un.gameRotationVector.real;
  float roll  = QUAT_RAD_TO_DEG * atan2(2.0f * (real * i + j * k), 1.0f - 2.0f * (i * i + j * j));
  float pitch = QUAT_RAD_TO_DEG * asin(fmaxf(-1.0f, fminf(1.0f, 2.0f * (real * j - k * i))));
  float yaw   = QUAT_RAD_TO_DEG * atan2(2.0f * (real * k + i * j), 1.0f - 2.0f * (j * j + k * k));
  
  printPadded(roll, 10);
  Serial.print(" ");
  printPadded(pitch, 10);
  Serial.print(" ");
  printPadded(yaw, 10);
  Serial.print("\r");
}

static void printPadded(float val, int width) {
  char buf[16];
  snprintf(buf, sizeof(buf), "%.2f", (double)val);
  int len = strlen(buf);
  for (int i = len; i < width; i++) Serial.print(" ");
  Serial.print(buf);
}
