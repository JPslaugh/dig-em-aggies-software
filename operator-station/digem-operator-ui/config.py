# Network configuration — change IPs here for laptop vs Pi deployment
NETWORK = {
    "relay1":   {"ip": "192.168.100.11", "port": 502},
    "relay2":   {"ip": "192.168.100.10", "port": 502},
    "teensy1":  {"ip": "192.168.100.60", "port": 5000},  # TBD — assign static IP
    "teensy2":  {"ip": "192.168.100.61", "port": 5001},  # TBD — assign static IP
}

MQTT = {
    "broker": "",           # TBC provides this at competition
    "port": 1883,
    "topic": "nabc26/dig_em_aggies",
    "rate_hz": 0.1,
}

# Controls password
CONTROLS_PASSWORD = "digem2026"

# System state machine states
class State:
    ESTOPPED = "E-STOPPED"
    IDLE     = "IDLE"
    STARTING = "STARTING"
    RUNNING  = "RUNNING"

# IO thresholds for each sensor (Low Alarm, Low Warn, High Warn, High Alarm, units)
IO_THRESHOLDS = {
    "RPM":        {"low_alarm": -1,   "low_warn": -1,   "high_warn": 17,   "high_alarm": 20,   "unit": "RPM"},
    "Flow":       {"low_alarm": -1,   "low_warn": -1,   "high_warn": 17,   "high_alarm": 20,   "unit": "L/min"},
    "Depth":      {"low_alarm": -1,   "low_warn": -1,   "high_warn": 1.3,  "high_alarm": 1.5,  "unit": "m"},
    "Roll":       {"low_alarm": -7,   "low_warn": -5,   "high_warn": 5,    "high_alarm": 7,    "unit": "deg"},
    "Pitch":      {"low_alarm": -7,   "low_warn": -5,   "high_warn": 5,    "high_alarm": 7,    "unit": "deg"},
    "Yaw":        {"low_alarm": -180, "low_warn": -180, "high_warn": 180,  "high_alarm": 180,  "unit": "deg"},
    "Relay1_V":   {"low_alarm": 20,   "low_warn": 22,   "high_warn": 26,   "high_alarm": 28,   "unit": "V"},
    "Relay1_A":   {"low_alarm": 0,    "low_warn": 0,    "high_warn": 12,   "high_alarm": 14,   "unit": "A"},
    "Relay2_V":   {"low_alarm": 20,   "low_warn": 22,   "high_warn": 26,   "high_alarm": 28,   "unit": "V"},
    "Relay2_A":   {"low_alarm": 0,    "low_warn": 0,    "high_warn": 5,    "high_alarm": 6,    "unit": "A"},
    "Rail24V_V":  {"low_alarm": 22,   "low_warn": 23,   "high_warn": 25,   "high_alarm": 26,   "unit": "V"},
    "Rail24V_A":  {"low_alarm": 0,    "low_warn": 0,    "high_warn": 5.5,  "high_alarm": 6.5,  "unit": "A"},
    "Rail12V_V":  {"low_alarm": 10,   "low_warn": 11,   "high_warn": 13,   "high_alarm": 14,   "unit": "V"},
    "Rail12V_A":  {"low_alarm": 0,    "low_warn": 0,    "high_warn": 11,   "high_alarm": 13,   "unit": "A"},
    "Encl_Temp1": {"low_alarm": -10,  "low_warn": 0,    "high_warn": 60,   "high_alarm": 70,   "unit": "°C"},
    "Encl_Temp2": {"low_alarm": -10,  "low_warn": 0,    "high_warn": 60,   "high_alarm": 70,   "unit": "°C"},
}

# Stale data timeout (seconds)
STALE_TIMEOUT = 10
