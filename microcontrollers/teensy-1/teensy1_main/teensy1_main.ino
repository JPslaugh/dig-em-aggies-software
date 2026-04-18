#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>
#include <math.h>

// ── Network ───────────────────────────────────────────────────────────────────
byte      mac[]      = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x01 };
IPAddress ip         (192, 168, 100, 60);
IPAddress gateway    (192, 168, 100,  1);
IPAddress subnet     (255, 255, 255,  0);
IPAddress broadcast  (192, 168, 100, 255);
const uint16_t UDP_PORT      = 5000;
const uint32_t BROADCAST_MS  = 500;   // 2 Hz
EthernetUDP udp;

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_RPM  2
#define PIN_FLOW 3

// ── RPM config ────────────────────────────────────────────────────────────────
// Set to the number of gear teeth on the cutterhead encoder gear.
// To calibrate: spin cutterhead one full revolution by hand, count serial pulses.
#define PULSES_PER_REV 1

// ── Pulse counters (ISR) ──────────────────────────────────────────────────────
volatile uint32_t _rpm_pulses  = 0;
volatile uint32_t _flow_pulses = 0;

void rpm_isr()  { _rpm_pulses++;  }
void flow_isr() { _flow_pulses++; }

// ── IMU ───────────────────────────────────────────────────────────────────────
Adafruit_BNO08x  imu(-1);
sh2_SensorValue_t imu_val;

float imu_roll  = 0.0f;
float imu_pitch = 0.0f;
float imu_yaw   = 0.0f;
bool  imu_ok    = false;

void imu_enable_reports() {
    imu.enableReport(SH2_GAME_ROTATION_VECTOR, 20000); // 50 Hz internal
}

void update_imu() {
    if (!imu_ok) return;
    if (imu.wasReset()) imu_enable_reports();
    if (!imu.getSensorEvent(&imu_val)) return;
    if (imu_val.sensorId != SH2_GAME_ROTATION_VECTOR) return;

    float i    = imu_val.un.gameRotationVector.i;
    float j    = imu_val.un.gameRotationVector.j;
    float k    = imu_val.un.gameRotationVector.k;
    float real = imu_val.un.gameRotationVector.real;

    // Quaternion → Euler (radians) — matches MQTT packet format directly
    imu_roll  = atan2(2.0f * (real * i + j * k), 1.0f - 2.0f * (i * i + j * j));
    imu_pitch = asin(fmaxf(-1.0f, fminf(1.0f,   2.0f * (real * j - k * i))));
    imu_yaw   = atan2(2.0f * (real * k + i * j), 1.0f - 2.0f * (j * j + k * k));
}

// ── TF-Luna LiDAR (I2C) ───────────────────────────────────────────────────────
#define TFLUNA_ADDR 0x10

float read_depth_cm() {
    Wire.beginTransmission(TFLUNA_ADDR);
    Wire.write(0x00);
    if (Wire.endTransmission(false) != 0) return -1.0f;
    Wire.requestFrom((uint8_t)TFLUNA_ADDR, (uint8_t)2);
    if (Wire.available() < 2) return -1.0f;
    uint16_t dist = (uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8);
    return (float)dist;
}

// ── UDP broadcast ─────────────────────────────────────────────────────────────
void broadcast_packet(float rpm, float flow_lpm, float depth_cm) {
    char buf[256];
    snprintf(buf, sizeof(buf),
        "{\"rpm\":%.1f,\"flow_lpm\":%.3f,"
        "\"roll\":%.4f,\"pitch\":%.4f,\"yaw\":%.4f,"
        "\"depth_cm\":%.1f,\"uptime_ms\":%lu}",
        rpm, flow_lpm,
        imu_roll, imu_pitch, imu_yaw,
        depth_cm, millis());

    udp.beginPacket(broadcast, UDP_PORT);
    udp.write((uint8_t*)buf, strlen(buf));
    udp.endPacket();
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000);
    Serial.println("Teensy 1 — Sensor Firmware");

    // Ethernet
    Ethernet.begin(mac, ip, gateway, gateway, subnet);
    delay(500);
    Serial.print("IP: ");
    Serial.println(Ethernet.localIP());
    Serial.print("Link: ");
    Serial.println(Ethernet.linkStatus() == LinkON ? "UP" : "DOWN");
    udp.begin(UDP_PORT);

    // I2C
    Wire.begin();
    Wire.setClock(100000);

    // IMU
    if (!imu.begin_I2C()) {
        Serial.println("BNO08x: NOT FOUND — check wiring");
    } else {
        imu_enable_reports();
        imu_ok = true;
        Serial.println("BNO08x: OK");
    }

    // TF-Luna
    float d = read_depth_cm();
    if (d < 0.0f) {
        Serial.println("TF-Luna: NOT FOUND — check wiring");
    } else {
        Serial.print("TF-Luna: OK  (");
        Serial.print(d, 1);
        Serial.println(" cm)");
    }

    // Interrupts — FALLING edge (PNP NO through PC817 optocoupler)
    pinMode(PIN_RPM,  INPUT);
    pinMode(PIN_FLOW, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_RPM),  rpm_isr,  FALLING);
    attachInterrupt(digitalPinToInterrupt(PIN_FLOW), flow_isr, FALLING);

    Serial.println("Ready — broadcasting at 2 Hz");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    update_imu();

    static uint32_t last_tx = 0;
    uint32_t now = millis();

    if (now - last_tx >= BROADCAST_MS) {
        float dt = (now - last_tx) / 1000.0f;
        last_tx  = now;

        noInterrupts();
        uint32_t rpm_p  = _rpm_pulses;  _rpm_pulses  = 0;
        uint32_t flow_p = _flow_pulses; _flow_pulses = 0;
        interrupts();

        float rpm      = (rpm_p  / (float)PULSES_PER_REV) * (60.0f / dt);
        float flow_lpm = (flow_p / dt) / 7.5f;   // FL-608: Q(L/min) = F(Hz) / 7.5
        float depth_cm = read_depth_cm();

        broadcast_packet(rpm, flow_lpm, depth_cm);

        Serial.print("RPM:");    Serial.print(rpm,      1);
        Serial.print(" Flow:");  Serial.print(flow_lpm, 3);
        Serial.print(" Depth:"); Serial.print(depth_cm, 1);
        Serial.print(" R:");     Serial.print(imu_roll,  4);
        Serial.print(" P:");     Serial.print(imu_pitch, 4);
        Serial.print(" Y:");     Serial.println(imu_yaw, 4);
    }
}
