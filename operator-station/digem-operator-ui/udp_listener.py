"""
UDP Listener
Receives JSON broadcast packets from Teensy 1 (port 5000) and Teensy 2 (port 5001).
Emits Qt signals so data flows safely into the main thread.
"""

import socket
import json
import math
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from config import NETWORK, STALE_TIMEOUT


class UDPListener(QObject):
    sensor_received    = pyqtSignal(str, float)         # key, value
    power_received     = pyqtSignal(str, float, float)  # key, voltage, current
    connection_changed = pyqtSignal(str, bool, bool)    # device, connected, stale

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running      = False
        self._last_seen    = {"teensy1": 0.0, "teensy2": 0.0}
        self._connected    = {"teensy1": False, "teensy2": False}

    def start(self):
        self._running = True
        threading.Thread(target=self._listen, args=("teensy1",), daemon=True).start()
        threading.Thread(target=self._listen, args=("teensy2",), daemon=True).start()
        threading.Thread(target=self._stale_loop, daemon=True).start()

    def stop(self):
        self._running = False

    def _listen(self, device: str):
        port = NETWORK[device]["port"]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind(("", port))

        while self._running:
            try:
                data, _ = sock.recvfrom(1024)
                pkt = json.loads(data.decode())
                self._last_seen[device] = time.time()

                if not self._connected[device]:
                    self._connected[device] = True
                    self.connection_changed.emit(device, True, False)

                if device == "teensy1":
                    self._parse_teensy1(pkt)
                else:
                    self._parse_teensy2(pkt)

            except socket.timeout:
                pass
            except Exception:
                pass

        sock.close()

    def _parse_teensy1(self, pkt: dict):
        # IMU arrives in radians — convert to degrees for display
        if "roll"  in pkt: self.sensor_received.emit("Roll",  math.degrees(pkt["roll"]))
        if "pitch" in pkt: self.sensor_received.emit("Pitch", math.degrees(pkt["pitch"]))
        if "yaw"   in pkt: self.sensor_received.emit("Yaw",   math.degrees(pkt["yaw"]))

        if "rpm"      in pkt: self.sensor_received.emit("RPM",  pkt["rpm"])
        if "flow_lpm" in pkt: self.sensor_received.emit("Flow", pkt["flow_lpm"])
        if "depth_cm" in pkt:
            depth = pkt["depth_cm"] if pkt["depth_cm"] >= 0 else 0.0
            self.sensor_received.emit("Depth", depth / 100.0)  # cm → m

    def _parse_teensy2(self, pkt: dict):
        if "ina_relay1_v" in pkt:
            self.power_received.emit("relay1", pkt["ina_relay1_v"], pkt["ina_relay1_a"])
        if "ina_relay2_v" in pkt:
            self.power_received.emit("relay2", pkt["ina_relay2_v"], pkt["ina_relay2_a"])
        if "ina_24v_v" in pkt:
            self.power_received.emit("24v", pkt["ina_24v_v"], pkt["ina_24v_a"])
        if "ina_12v_v" in pkt:
            self.power_received.emit("12v", pkt["ina_12v_v"], pkt["ina_12v_a"])
        if "temp1_c" in pkt:
            self.sensor_received.emit("Encl_Temp1", pkt["temp1_c"])
        if "temp2_c" in pkt:
            self.sensor_received.emit("Encl_Temp2", pkt["temp2_c"])

    def _stale_loop(self):
        while self._running:
            time.sleep(2.0)
            now = time.time()
            for device in ("teensy1", "teensy2"):
                last = self._last_seen[device]
                if self._connected[device] and last > 0 and (now - last) > STALE_TIMEOUT:
                    self._connected[device] = False
                    self.connection_changed.emit(device, False, True)
