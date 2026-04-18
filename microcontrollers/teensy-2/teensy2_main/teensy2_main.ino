#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>
#include <Wire.h>
#include <Adafruit_INA260.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ── Network ───────────────────────────────────────────────────────────────────
byte      mac[]     = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x02 };
IPAddress ip        (192, 168, 100, 61);
IPAddress gateway   (192, 168, 100,  1);
IPAddress subnet    (255, 255, 255,  0);
IPAddress broadcast (192, 168, 100, 255);
const uint16_t UDP_PORT     = 5001;
const uint32_t BROADCAST_MS = 1000;  // 1 Hz
EthernetUDP udp;

// ── INA260 power monitors ─────────────────────────────────────────────────────
Adafruit_INA260 ina_relay1;  // 0x40 — Relay 1 24V rail
Adafruit_INA260 ina_relay2;  // 0x41 — Relay 2 24V rail
Adafruit_INA260 ina_24v;     // 0x44 — Main 24V supply
Adafruit_INA260 ina_12v;     // 0x45 — Main 12V supply

bool ina_relay1_ok = false;
bool ina_relay2_ok = false;
bool ina_24v_ok    = false;
bool ina_12v_ok    = false;

struct PowerReading {
    float voltage;
    float current;
    float watts;
};

PowerReading read_ina(Adafruit_INA260 &ina, bool ok) {
    if (!ok) return {-1.0f, -1.0f, -1.0f};
    float v = ina.readBusVoltage()  / 1000.0f;  // mV → V
    float a = ina.readCurrent()     / 1000.0f;  // mA → A
    float w = ina.readPower()       / 1000.0f;  // mW → W
    return {v, a, w};
}

// ── DS18B20 temperature ───────────────────────────────────────────────────────
#define PIN_ONEWIRE 4
OneWire           one_wire(PIN_ONEWIRE);
DallasTemperature temp_sensors(&one_wire);
int               temp_count = 0;

// ── UDP broadcast ─────────────────────────────────────────────────────────────
void broadcast_packet(PowerReading r1, PowerReading r2,
                      PowerReading r24, PowerReading r12,
                      float t1, float t2) {
    char buf[512];
    snprintf(buf, sizeof(buf),
        "{"
        "\"ina_relay1_v\":%.2f,\"ina_relay1_a\":%.3f,\"ina_relay1_w\":%.2f,"
        "\"ina_relay2_v\":%.2f,\"ina_relay2_a\":%.3f,\"ina_relay2_w\":%.2f,"
        "\"ina_24v_v\":%.2f,\"ina_24v_a\":%.3f,\"ina_24v_w\":%.2f,"
        "\"ina_12v_v\":%.2f,\"ina_12v_a\":%.3f,\"ina_12v_w\":%.2f,"
        "\"temp1_c\":%.2f,\"temp2_c\":%.2f,"
        "\"uptime_ms\":%lu"
        "}",
        r1.voltage,  r1.current,  r1.watts,
        r2.voltage,  r2.current,  r2.watts,
        r24.voltage, r24.current, r24.watts,
        r12.voltage, r12.current, r12.watts,
        t1, t2, millis());

    udp.beginPacket(broadcast, UDP_PORT);
    udp.write((uint8_t*)buf, strlen(buf));
    udp.endPacket();
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000);
    Serial.println("Teensy 2 — Power Monitor Firmware");

    // Ethernet
    Ethernet.begin(mac, ip, gateway, gateway, subnet);
    delay(2000);  // wait for link negotiation
    Serial.print("IP: ");
    Serial.println(Ethernet.localIP());
    udp.begin(UDP_PORT);

    // I2C
    Wire.begin();
    Wire.setClock(100000);

    // INA260s
    ina_relay1_ok = ina_relay1.begin(0x40);
    Serial.println(ina_relay1_ok ? "INA260 Relay1 (0x40): OK" : "INA260 Relay1 (0x40): NOT FOUND");

    ina_relay2_ok = ina_relay2.begin(0x41);
    Serial.println(ina_relay2_ok ? "INA260 Relay2 (0x41): OK" : "INA260 Relay2 (0x41): NOT FOUND");

    ina_24v_ok = ina_24v.begin(0x44);
    Serial.println(ina_24v_ok ? "INA260 24V   (0x44): OK" : "INA260 24V   (0x44): NOT FOUND");

    ina_12v_ok = ina_12v.begin(0x45);
    Serial.println(ina_12v_ok ? "INA260 12V   (0x45): OK" : "INA260 12V   (0x45): NOT FOUND");

    // DS18B20
    temp_sensors.begin();
    temp_count = temp_sensors.getDeviceCount();
    Serial.print("DS18B20 sensors found: ");
    Serial.println(temp_count);

    Serial.println("Ready — broadcasting at 1 Hz");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    static uint32_t last_tx = 0;
    uint32_t now = millis();

    if (now - last_tx >= BROADCAST_MS) {
        last_tx = now;

        PowerReading r1  = read_ina(ina_relay1, ina_relay1_ok);
        PowerReading r2  = read_ina(ina_relay2, ina_relay2_ok);
        PowerReading r24 = read_ina(ina_24v,    ina_24v_ok);
        PowerReading r12 = read_ina(ina_12v,    ina_12v_ok);

        temp_sensors.requestTemperatures();
        float t1 = temp_count > 0 ? temp_sensors.getTempCByIndex(0) : -127.0f;
        float t2 = temp_count > 1 ? temp_sensors.getTempCByIndex(1) : -127.0f;

        broadcast_packet(r1, r2, r24, r12, t1, t2);

        Serial.print("Link:"); Serial.print(Ethernet.linkStatus() == LinkON ? "UP" : "DOWN");
        Serial.print(" R1:");  Serial.print(r1.voltage,  2); Serial.print("V ");
                              Serial.print(r1.current,  3); Serial.print("A ");
                              Serial.print(r1.watts,    2); Serial.print("W  ");
        Serial.print("R2:");  Serial.print(r2.voltage,  2); Serial.print("V ");
                              Serial.print(r2.current,  3); Serial.print("A ");
                              Serial.print(r2.watts,    2); Serial.print("W  ");
        Serial.print("24V:"); Serial.print(r24.voltage, 2); Serial.print("V ");
                              Serial.print(r24.current, 3); Serial.print("A  ");
        Serial.print("12V:"); Serial.print(r12.voltage, 2); Serial.print("V ");
                              Serial.print(r12.current, 3); Serial.print("A  ");
        Serial.print("T1:");  Serial.print(t1, 2); Serial.print("C  ");
        Serial.print("T2:");  Serial.println(t2, 2);
    }
}
