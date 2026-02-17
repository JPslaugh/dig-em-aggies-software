#!/usr/bin/env python3
import smbus2
import socket
import subprocess
import time
from PIL import Image, ImageDraw

bus = smbus2.SMBus(1)
addr = 0x3c

def cmd(c):
    bus.write_byte_data(addr, 0x00, c)

def data(d):
    bus.write_byte_data(addr, 0x40, d)

def init():
    for c in [0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0xFF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0xAF]:
        cmd(c)

def show(img):
    pixels = list(img.getdata())
    for page in range(8):
        cmd(0xB0 + page)
        cmd(0x02)
        cmd(0x10)
        for x in range(128):
            byte = 0
            for bit in range(8):
                if pixels[(page * 8 + bit) * 128 + x]:
                    byte |= (1 << bit)
            data(byte)

def get_ip():
    try:
        result = subprocess.run(["ip", "-4", "addr", "show", "eth0"], capture_output=True, text=True)
        return [l.strip().split()[1].split("/")[0] for l in result.stdout.split("\n") if "inet " in l][0]
    except:
        return "No IP"

def get_temp():
    try:
        result = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True)
        return result.stdout.strip().replace("temp=", "")
    except:
        return "N/A"

init()
hostname = socket.gethostname()
password = "digem2026"

while True:
    ip = get_ip()
    temp = get_temp()

    img = Image.new("1", (128, 64), 0)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), hostname, fill=1)
    draw.line((0, 12, 127, 12), fill=1)
    draw.text((0, 18), "IP: " + ip, fill=1)
    draw.text((0, 33), "PW: " + password, fill=1)
    draw.text((0, 50), "Temp: " + temp, fill=1)
    show(img)

    time.sleep(5)
