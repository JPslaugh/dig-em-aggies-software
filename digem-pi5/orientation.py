#!/usr/bin/env python3
import board
import busio
import math
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
bno = BNO08X_I2C(i2c)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

print('Reading orientation (Ctrl+C to stop)...')
print('      Roll      Pitch        Yaw')
print('-' * 34)

while True:
    quat = bno.quaternion
    if quat is None:
        continue
    i, j, k, real = quat

    # Convert quaternion to Euler angles (degrees)
    roll  = math.degrees(math.atan2(2*(real*i + j*k), 1 - 2*(i*i + j*j)))
    pitch = math.degrees(math.asin(max(-1, min(1, 2*(real*j - k*i)))))
    yaw   = math.degrees(math.atan2(2*(real*k + i*j), 1 - 2*(j*j + k*k)))

    print(f'{roll:>10.2f} {pitch:>10.2f} {yaw:>10.2f}', end='\r')
