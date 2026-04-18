#include <NativeEthernet.h>

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x01 };

IPAddress ip(192, 168, 100, 60);
IPAddress gateway(192, 168, 100, 1);
IPAddress subnet(255, 255, 255, 0);

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);

  Serial.println("Teensy 1 — Ethernet Test");
  Serial.println("Initializing...");

  Ethernet.begin(mac, ip, gateway, gateway, subnet);

  delay(1000);

  if (Ethernet.linkStatus() == LinkON) {
    Serial.println("Ethernet link: UP");
  } else {
    Serial.println("Ethernet link: DOWN — check cable/switch");
  }

  Serial.print("IP Address: ");
  Serial.println(Ethernet.localIP());
}

void loop() {
  Serial.print("Link: ");
  Serial.println(Ethernet.linkStatus() == LinkON ? "UP" : "DOWN");
  delay(2000);
}
