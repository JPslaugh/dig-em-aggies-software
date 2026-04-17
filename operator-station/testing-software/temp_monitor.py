#!/usr/bin/env python3
import subprocess
import time

def get_temp():
    result = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True)
    return float(result.stdout.strip().replace("temp=", "").replace("'C", ""))

def play_warning():
    subprocess.Popen(["aplay", "-D", "plughw:2,0", "/home/digem/warning_temp.wav"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

prev_temp = get_temp()
print(f"Monitoring started. Current temp: {prev_temp}C")

while True:
    time.sleep(5)
    curr_temp = get_temp()
    if curr_temp > prev_temp:
        print(f"Temp increased: {prev_temp}C -> {curr_temp}C")
        play_warning()
    prev_temp = curr_temp
