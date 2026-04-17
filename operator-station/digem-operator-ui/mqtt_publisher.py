"""
MQTT Publisher
Publishes navigation telemetry to TBC at 0.1 Hz when mining flag is active.

JSON format per NaBC 2026 Full Rules Section 9d:
{
    "team":      <string>,
    "timestamp": <UNIX float>,
    "mining":    <bool>,
    "chainage":  <float, metres>        — linear distance traveled (= depth for vertical bore)
    "easting":   <float, metres>        — relative to TBC site coordinate system
    "northing":  <float, metres>        — relative to TBC site coordinate system
    "elevation": <float, metres>        — negative = below surface
    "roll":      <float, radians>,
    "pitch":     <float, radians>,
    "heading":   <float, radians>,      — 0 = North, positive = East
    "extra": {
        "rpm":         <float>,
        "flow_lpm":    <float>,
        "depth_m":     <float>,
        "encl_temp1":  <float>,
        "encl_temp2":  <float>,
        "relay1_v":    <float>,
        "relay1_a":    <float>,
        "relay2_v":    <float>,
        "relay2_a":    <float>,
        "rail24v_v":   <float>,
        "rail24v_a":   <float>,
        "rail12v_v":   <float>,
        "rail12v_a":   <float>,
    }
}

Notes:
- roll/pitch/heading converted from degrees to radians before publishing
- chainage = depth (vertical bore — linear distance = how far down we've gone)
- easting/northing = 0.0 until TBC provides site coordinate reference points
- elevation = -depth (surface = 0, down = negative)
- Only publishes when mining=True
"""

import math
import time
import json
import logging

from PyQt5.QtCore import QTimer, QObject, pyqtSignal

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

from config import MQTT

log = logging.getLogger(__name__)

TEAM_NAME = "dig_em_aggies"


class MQTTPublisher(QObject):

    status_changed = pyqtSignal(str)   # emitted on connect/disconnect/error

    def __init__(self, parent=None):
        super().__init__(parent)

        # Latest sensor values — updated by MainWindow
        self._sensors = {
            "RPM": 0.0, "Flow": 0.0, "Depth": 0.0,
            "Roll": 0.0, "Pitch": 0.0, "Yaw": 0.0,
            "Encl_Temp1": 0.0, "Encl_Temp2": 0.0,
        }
        self._power = {
            "relay1": (0.0, 0.0),
            "relay2": (0.0, 0.0),
            "24v":    (0.0, 0.0),
            "12v":    (0.0, 0.0),
        }
        self._mining  = False
        self._connected = False
        self._client  = None

        # Publish timer — 0.1 Hz = every 10 seconds
        interval_ms = int(1000 / MQTT["rate_hz"])
        self._timer = QTimer()
        self._timer.timeout.connect(self._publish)
        self._timer.start(interval_ms)

        self._connect()


    def update_sensor(self, key: str, value: float):
        if key in self._sensors:
            self._sensors[key] = value

    def update_power(self, key: str, voltage: float, current: float):
        if key in self._power:
            self._power[key] = (voltage, current)

    def set_mining(self, active: bool):
        self._mining = active

    def set_broker(self, host: str, port: int = 1883):
        """Call when TBC provides broker address at competition."""
        MQTT["broker"] = host
        MQTT["port"]   = port
        self._connect()


    def _connect(self):
        if not MQTT_AVAILABLE:
            self.status_changed.emit("paho-mqtt not installed")
            return
        if not MQTT["broker"]:
            self.status_changed.emit("MQTT broker address not set")
            return

        try:
            self._client = mqtt.Client(client_id=TEAM_NAME, protocol=mqtt.MQTTv5)
            self._client.on_connect    = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.connect_async(MQTT["broker"], MQTT["port"], keepalive=60)
            self._client.loop_start()
        except Exception as e:
            self.status_changed.emit(f"MQTT connect error: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        self._connected = (rc == 0)
        if self._connected:
            self.status_changed.emit(f"MQTT connected → {MQTT['broker']}")
        else:
            self.status_changed.emit(f"MQTT connect failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        self.status_changed.emit("MQTT disconnected")

    def _build_payload(self) -> dict:
        depth   = self._sensors["Depth"]
        roll_r  = math.radians(self._sensors["Roll"])
        pitch_r = math.radians(self._sensors["Pitch"])
        # Heading: BNO085 yaw is 0=North, positive=East — matches TBC convention
        heading_r = math.radians(self._sensors["Yaw"])

        r1v, r1a = self._power["relay1"]
        r2v, r2a = self._power["relay2"]
        v24v, a24v = self._power["24v"]
        v12v, a12v = self._power["12v"]

        return {
            "team":      TEAM_NAME,
            "timestamp": time.time(),
            "mining":    self._mining,
            "chainage":  round(depth, 4),           # vertical bore: chainage = depth
            "easting":   0.0,                        # TBD — TBC site coordinates
            "northing":  0.0,                        # TBD — TBC site coordinates
            "elevation": round(-depth, 4),           # below surface = negative
            "roll":      round(roll_r, 6),
            "pitch":     round(pitch_r, 6),
            "heading":   round(heading_r, 6),
            "extra": {
                "rpm":        round(self._sensors["RPM"],        2),
                "flow_lpm":   round(self._sensors["Flow"],       2),
                "depth_m":    round(depth,                       4),
                "encl_temp1": round(self._sensors["Encl_Temp1"], 2),
                "encl_temp2": round(self._sensors["Encl_Temp2"], 2),
                "relay1_v":   round(r1v,  2),
                "relay1_a":   round(r1a,  2),
                "relay2_v":   round(r2v,  2),
                "relay2_a":   round(r2a,  2),
                "rail24v_v":  round(v24v, 2),
                "rail24v_a":  round(a24v, 2),
                "rail12v_v":  round(v12v, 2),
                "rail12v_a":  round(a12v, 2),
            }
        }

    def _publish(self):
        if not self._mining:
            return
        if not MQTT_AVAILABLE or not self._connected or not self._client:
            return

        try:
            payload = json.dumps(self._build_payload())
            result  = self._client.publish(MQTT["topic"], payload, qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.status_changed.emit(f"MQTT publish error (rc={result.rc})")
        except Exception as e:
            self.status_changed.emit(f"MQTT publish exception: {e}")

    def shutdown(self):
        self._timer.stop()
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
