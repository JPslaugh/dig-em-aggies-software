#!/usr/bin/env python3
"""
Quick 3D cube test visualizer — BNO085 via Teensy 4.1
Reads Roll/Pitch/Yaw from /dev/ttyACM0 at 115200 baud
No OpenGL needed — pure pygame software render
"""
import pygame, serial, threading, math, sys

PORT     = '/dev/ttyACM0'
BAUD     = 115200
W, H     = 800, 600

# Cube vertices
VERTS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1)]
EDGES = [(0,1),(1,2),(2,3),(3,0),
         (4,5),(5,6),(6,7),(7,4),
         (0,4),(1,5),(2,6),(3,7)]

# Shared state
_roll = _pitch = _yaw = 0.0
_lock = threading.Lock()
_connected = False

# Zero offset — set by pressing SPACE
_zero_roll = _zero_pitch = _zero_yaw = 0.0

def _read_serial():
    global _roll, _pitch, _yaw, _connected
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        _connected = True
        buf = b''
        while True:
            chunk = ser.read(256)
            if not chunk:
                continue
            buf += chunk
            while b'\r' in buf:
                line, buf = buf.split(b'\r', 1)
                parts = line.decode('utf-8', errors='ignore').strip().split()
                if len(parts) == 3:
                    try:
                        r, p, y = float(parts[0]), float(parts[1]), float(parts[2])
                        with _lock:
                            _roll, _pitch, _yaw = r, p, y
                    except ValueError:
                        pass
    except Exception as e:
        print(f"Serial error: {e}")

def _mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def _apply(m, v):
    return [sum(m[i][j]*v[j] for j in range(3)) for i in range(3)]

def _rx(a):
    c,s = math.cos(a), math.sin(a)
    return [[1,0,0],[0,c,-s],[0,s,c]]

def _ry(a):
    c,s = math.cos(a), math.sin(a)
    return [[c,0,s],[0,1,0],[-s,0,c]]

def _rz(a):
    c,s = math.cos(a), math.sin(a)
    return [[c,-s,0],[s,c,0],[0,0,1]]

def _project(v):
    z = v[2] + 5.0
    return (int(v[0] * 400 / z + W / 2),
            int(-v[1] * 400 / z + H / 2))

def main():
    threading.Thread(target=_read_serial, daemon=True).start()

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("BNO085 Cube Test")
    font_lg = pygame.font.SysFont("monospace", 22, bold=True)
    font_sm = pygame.font.SysFont("monospace", 16)
    clock  = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                global _zero_roll, _zero_pitch, _zero_yaw
                with _lock:
                    _zero_roll  = _roll
                    _zero_pitch = _pitch
                    _zero_yaw   = _yaw

        with _lock:
            rd = _roll  - _zero_roll
            pd = _pitch - _zero_pitch
            yd = _yaw   - _zero_yaw
            r, p, y = math.radians(rd), math.radians(-pd), math.radians(yd)

        # Remap sensor axes to screen axes:
        # Yaw  (sensor Z = up)      → _ry (screen Y = up)
        # Pitch (sensor Y = left)   → _rx (screen X = horizontal)
        # Roll  (sensor X = forward)→ _rz (screen Z = depth)
        mat = _mul(_ry(-y), _mul(_rx(r), _rz(p)))
        pts = [_project(_apply(mat, list(v))) for v in VERTS]

        screen.fill((18, 18, 18))

        # Draw edges — back edges dimmer
        for i, (a, b) in enumerate(EDGES):
            color = (0, 160, 220) if i < 4 else (0, 220, 140) if i < 8 else (220, 180, 0)
            pygame.draw.line(screen, color, pts[a], pts[b], 2)

        # Vertex dots
        for pt in pts:
            pygame.draw.circle(screen, (255, 255, 255), pt, 4)

        # Angle readout
        screen.blit(font_lg.render(f"Pitch: {rd:8.2f}°", True, (200, 200, 200)), (20, 20))
        screen.blit(font_lg.render(f"Roll:  {pd:8.2f}°", True, (200, 200, 200)), (20, 48))
        screen.blit(font_lg.render(f"Yaw:   {yd:8.2f}°", True, (200, 200, 200)), (20, 76))

        # Legend
        pygame.draw.line(screen, (0, 160, 220), (20, 130), (50, 130), 2)
        screen.blit(font_sm.render("Back face", True, (120,120,120)), (58, 122))
        pygame.draw.line(screen, (0, 220, 140), (20, 150), (50, 150), 2)
        screen.blit(font_sm.render("Front face", True, (120,120,120)), (58, 142))
        pygame.draw.line(screen, (220, 180, 0), (20, 170), (50, 170), 2)
        screen.blit(font_sm.render("Connecting", True, (120,120,120)), (58, 162))

        screen.blit(font_sm.render("SPACE to zero  |  ESC to quit", True, (80, 80, 80)), (20, H - 28))

        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
