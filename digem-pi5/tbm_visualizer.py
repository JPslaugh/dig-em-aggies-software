#!/usr/bin/env python3
"""
TBM (Tunnel Boring Machine) 3D Orientation Visualizer
Dig 'Em Aggies – Not-a-Boring Competition 2026

Hardware: BNO085 IMU on I2C bus 1 (0x4A), Raspberry Pi 5
Renders a 3D cylinder whose orientation matches the physical sensor in real time.

Uses pygame GLES 3.1 context + custom GLSL ES 3.00 shaders (required for Pi 5
VideoCore VII GPU which only supports OpenGL ES natively, not desktop OpenGL).
GLU is NOT used — cylinder geometry is built from triangle strips manually.

Run: SDL_VIDEODRIVER=wayland python3 tbm_visualizer.py
"""

import os, sys, math, threading, time, ctypes
import numpy as np
import pygame
from pygame.locals import OPENGL, DOUBLEBUF, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *

import board, busio
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C

os.environ.setdefault('SDL_VIDEODRIVER', 'wayland')

# ── Shared sensor state ──────────────────────────────────────────────────────
_lock   = threading.Lock()
_quat   = (1.0, 0.0, 0.0, 0.0)   # (w, x, y, z)
_angles = (0.0, 0.0, 0.0)         # (roll, pitch, yaw) degrees

def _sensor_loop():
    global _quat, _angles
    try:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
        bno = BNO08X_I2C(i2c)
        bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)
        while True:
            q = bno.quaternion
            if q is not None:
                xi, xj, xk, real = q   # BNO085 returns (i, j, k, real)
                roll  = math.degrees(math.atan2(2*(real*xi + xj*xk), 1 - 2*(xi**2 + xj**2)))
                pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2*(real*xj - xk*xi)))))
                yaw   = math.degrees(math.atan2(2*(real*xk + xi*xj), 1 - 2*(xj**2 + xk**2)))
                with _lock:
                    _quat   = (real, xi, xj, xk)
                    _angles = (roll, pitch, yaw)
            time.sleep(0.02)   # 50 Hz
    except Exception as e:
        print(f"[sensor] {e}")

# ── Geometry ─────────────────────────────────────────────────────────────────
def build_cylinder(radius=0.36, length=1.7, segs=60):
    """
    Returns dict of float32 arrays with interleaved (x,y,z, nx,ny,nz).
    Cylinder axis is Z. Front face (cutter head) is at +Z.

    Sections:
      'body'   – tube walls (GL_TRIANGLE_STRIP)
      'back'   – rear end cap (GL_TRIANGLE_FAN)
      'front'  – front cap (GL_TRIANGLE_FAN)
      'ring'   – wider cutter ring at +Z (GL_TRIANGLE_STRIP)
      'spokes' – 4 cross-spokes on cutter face (GL_TRIANGLES, needs spoke_idx)
    """
    def ring_verts(r, z, nx, ny, nz_val, segs):
        pts = []
        for i in range(segs + 1):
            a = 2 * math.pi * i / segs
            c, s = math.cos(a), math.sin(a)
            pts += [c*r, s*r, z,  c*nx, s*ny, nz_val]
        return pts

    # Body
    body = []
    for i in range(segs + 1):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        body += [c*radius, s*radius, -length/2,  c, s, 0,
                 c*radius, s*radius,  length/2,  c, s, 0]

    # End caps (triangle fan: center vertex first)
    back  = [0, 0, -length/2,  0, 0, -1] + ring_verts(radius, -length/2, 0, 0, -1, segs)
    front = [0, 0,  length/2,  0, 0,  1] + ring_verts(radius,  length/2, 0, 0,  1, segs)

    # Cutter ring: wider band at +Z end
    cr = radius * 1.12
    cd = 0.09   # ring depth
    ring = []
    for i in range(segs + 1):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        ring += [c*cr, s*cr, length/2 - cd,  c, s, 0,
                 c*cr, s*cr, length/2,        c, s, 0]

    # Spokes: 4 flat rectangular bars across the cutter face
    spk_verts = []
    spk_idx   = []
    spoke_r   = radius * 0.97
    half_w    = 0.028
    zf        = length/2 + 0.002
    for k, deg in enumerate([0, 45, 90, 135]):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        b = k * 4
        spk_verts += [
            -c*spoke_r - s*half_w, -s*spoke_r + c*half_w, zf,  0, 0, 1,
            -c*spoke_r + s*half_w, -s*spoke_r - c*half_w, zf,  0, 0, 1,
             c*spoke_r - s*half_w,  s*spoke_r + c*half_w, zf,  0, 0, 1,
             c*spoke_r + s*half_w,  s*spoke_r - c*half_w, zf,  0, 0, 1,
        ]
        spk_idx += [b, b+1, b+2,  b+1, b+3, b+2]

    # Reference axis lines: X=red, Y=green, Z=blue (6 floats/vert: pos + color)
    axis_scale = 0.7
    axis_verts = [
        0,0,0,  1,0,0,   axis_scale,0,0,      1,0,0,   # X
        0,0,0,  0,1,0,   0,axis_scale,0,      0,1,0,   # Y
        0,0,0,  0,0,1,   0,0,axis_scale,      0,0,1,   # Z
    ]

    return {
        'body':      np.array(body,      dtype=np.float32),
        'back':      np.array(back,      dtype=np.float32),
        'front':     np.array(front,     dtype=np.float32),
        'ring':      np.array(ring,      dtype=np.float32),
        'spokes':    np.array(spk_verts, dtype=np.float32),
        'spoke_idx': np.array(spk_idx,   dtype=np.uint32),
        'axis':      np.array(axis_verts,dtype=np.float32),
    }

# ── Shaders ──────────────────────────────────────────────────────────────────
_MESH_VERT = b"""
#version 300 es
layout(location=0) in vec3 a_pos;
layout(location=1) in vec3 a_normal;
uniform mat4 u_mvp;
uniform mat4 u_model;
out vec3 v_pos;
out vec3 v_normal;
void main() {
    v_pos    = (u_model * vec4(a_pos, 1.0)).xyz;
    v_normal = mat3(u_model) * a_normal;
    gl_Position = u_mvp * vec4(a_pos, 1.0);
}
"""

_MESH_FRAG = b"""
#version 300 es
precision mediump float;
in vec3 v_pos;
in vec3 v_normal;
uniform vec3 u_color;
uniform vec3 u_light;
uniform vec3 u_eye;
out vec4 out_color;
void main() {
    vec3 n  = normalize(v_normal);
    vec3 l  = normalize(u_light - v_pos);
    vec3 v  = normalize(u_eye   - v_pos);
    vec3 h  = normalize(l + v);
    float diff = max(dot(n, l), 0.0);
    float spec = pow(max(dot(n, h), 0.0), 48.0);
    vec3 col = u_color * (0.22 + 0.68 * diff) + 0.25 * spec;
    out_color = vec4(clamp(col, 0.0, 1.0), 1.0);
}
"""

_LINE_VERT = b"""
#version 300 es
layout(location=0) in vec3 a_pos;
layout(location=1) in vec3 a_color;
uniform mat4 u_mvp;
out vec3 v_color;
void main() {
    v_color = a_color;
    gl_Position = u_mvp * vec4(a_pos, 1.0);
}
"""

_LINE_FRAG = b"""
#version 300 es
precision mediump float;
in vec3 v_color;
out vec4 out_color;
void main() { out_color = vec4(v_color, 1.0); }
"""

_TEXT_VERT = b"""
#version 300 es
layout(location=0) in vec2 a_pos;
layout(location=1) in vec2 a_uv;
uniform mat4 u_ortho;
out vec2 v_uv;
void main() { v_uv = a_uv; gl_Position = u_ortho * vec4(a_pos, 0.0, 1.0); }
"""

_TEXT_FRAG = b"""
#version 300 es
precision mediump float;
in vec2 v_uv;
uniform sampler2D u_tex;
out vec4 out_color;
void main() { out_color = texture(u_tex, v_uv); }
"""

def _compile(src, kind):
    s = glCreateShader(kind)
    glShaderSource(s, src)
    glCompileShader(s)
    if not glGetShaderiv(s, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(s).decode())
    return s

def _link(vert_src, frag_src):
    vs = _compile(vert_src, GL_VERTEX_SHADER)
    fs = _compile(frag_src, GL_FRAGMENT_SHADER)
    p  = glCreateProgram()
    glAttachShader(p, vs); glAttachShader(p, fs)
    glLinkProgram(p)
    if not glGetProgramiv(p, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(p).decode())
    glDeleteShader(vs); glDeleteShader(fs)
    return p

# ── Matrix math (row-major; upload with GL_TRUE to transpose) ────────────────
def _perspective(fov_deg, aspect, near, far):
    f  = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    nf = near - far
    return np.array([
        f/aspect, 0,              0,                     0,
        0,        f,              0,                     0,
        0,        0, (far+near)/nf,   2*far*near/nf,
        0,        0,             -1,                     0,
    ], np.float32).reshape(4, 4)

def _look_at(eye, at, up):
    eye = np.array(eye, np.float32)
    at  = np.array(at,  np.float32)
    up  = np.array(up,  np.float32)
    f = at - eye;  f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.array([
         r[0],  r[1],  r[2], -np.dot(r, eye),
         u[0],  u[1],  u[2], -np.dot(u, eye),
        -f[0], -f[1], -f[2],  np.dot(f, eye),
         0,     0,     0,     1,
    ], np.float32).reshape(4, 4)

def _ortho(l, r, b, t):
    return np.array([
        2/(r-l),       0,  0, -(r+l)/(r-l),
              0, 2/(t-b),  0, -(t+b)/(t-b),
              0,       0, -1,            0,
              0,       0,  0,            1,
    ], np.float32).reshape(4, 4)

def _quat_to_mat4(w, x, y, z):
    # Quaternion (w, x, y, z) → 4×4 rotation matrix (row-major)
    return np.array([
        1-2*(y*y+z*z),   2*(x*y+w*z),   2*(x*z-w*y), 0,
          2*(x*y-w*z), 1-2*(x*x+z*z),   2*(y*z+w*x), 0,
          2*(x*z+w*y),   2*(y*z-w*x), 1-2*(x*x+y*y), 0,
        0, 0, 0, 1,
    ], np.float32).reshape(4, 4)

# ── VAO helpers ───────────────────────────────────────────────────────────────
def _vao(data, idx=None):
    """Upload float32 array (interleaved pos+normal, 6 floats/vert) into a VAO."""
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
    glEnableVertexAttribArray(1)
    if idx is not None:
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, idx.nbytes, idx, GL_STATIC_DRAW)
    glBindVertexArray(0)
    return vao, len(data) // 6

# ── Text rendering (texture per label) ───────────────────────────────────────
def _surf_to_tex(surf):
    w, h  = surf.get_size()
    raw   = pygame.image.tostring(surf, 'RGBA', False)
    tex   = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tex, w, h

def _draw_label(prog, ortho_mat, tex, x, y, w, h):
    quad = np.array([x, y, 0,1,  x+w, y, 1,1,  x, y+h, 0,0,  x+w, y+h, 1,0], np.float32)
    idx  = np.array([0,1,2, 1,3,2], np.uint32)
    vao  = glGenVertexArrays(1); glBindVertexArray(vao)
    vbo  = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_DYNAMIC_DRAW)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
    glEnableVertexAttribArray(1)
    ebo = glGenBuffers(1); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, idx.nbytes, idx, GL_DYNAMIC_DRAW)
    glUseProgram(prog)
    glUniformMatrix4fv(glGetUniformLocation(prog, 'u_ortho'), 1, GL_TRUE, ortho_mat.flatten())
    glBindTexture(GL_TEXTURE_2D, tex)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
    glDisable(GL_BLEND)
    glBindVertexArray(0)
    glDeleteVertexArrays(1, [vao]); glDeleteBuffers(2, [vbo, ebo])

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    threading.Thread(target=_sensor_loop, daemon=True).start()

    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_ES)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

    W, H = 900, 660
    pygame.display.set_mode((W, H), OPENGL | DOUBLEBUF)
    pygame.display.set_caption("TBM Orientation – Dig 'Em Aggies")

    # Compile shader programs
    prog_mesh = _link(_MESH_VERT, _MESH_FRAG)
    prog_line = _link(_LINE_VERT, _LINE_FRAG)
    prog_text = _link(_TEXT_VERT, _TEXT_FRAG)

    # Build and upload geometry
    geo = build_cylinder()
    vao_body,  cnt_body  = _vao(geo['body'])
    vao_back,  cnt_back  = _vao(geo['back'])
    vao_front, cnt_front = _vao(geo['front'])
    vao_ring,  cnt_ring  = _vao(geo['ring'])
    vao_spk,   _         = _vao(geo['spokes'], geo['spoke_idx'])
    cnt_spk = len(geo['spoke_idx'])
    vao_axis, cnt_axis   = _vao(geo['axis'])

    # Matrices
    proj     = _perspective(45.0, W / H, 0.1, 100.0)
    view     = _look_at([0, 1.0, 3.8], [0, 0, 0], [0, 1, 0])
    ortho    = _ortho(0, W, 0, H)
    eye_pos  = np.array([0.0, 1.0, 3.8], np.float32)
    light    = np.array([4.0, 5.0, 5.0], np.float32)

    # Material colors
    STEEL  = np.array([0.70, 0.70, 0.76], np.float32)
    CAP    = np.array([0.55, 0.55, 0.60], np.float32)
    CUTTER = np.array([0.88, 0.35, 0.08], np.float32)
    SPOKE  = np.array([0.20, 0.20, 0.22], np.float32)

    # Fonts
    font_title = pygame.font.SysFont('monospace', 24, bold=True)
    font_val   = pygame.font.SysFont('monospace', 22, bold=True)
    font_hint  = pygame.font.SysFont('monospace', 15)

    # Static labels (cached textures)
    title_surf = font_title.render("DIG 'EM AGGIES  |  TBM ORIENTATION", True, (210, 160, 160))
    hint_surf  = font_hint.render("ESC to quit", True, (100, 75, 75))
    tex_title, tw_t, th_t = _surf_to_tex(title_surf)
    tex_hint,  tw_h, th_h = _surf_to_tex(hint_surf)

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.05, 0.0, 0.0, 1.0)

    clock   = pygame.time.Clock()
    running = True

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT or (ev.type == KEYDOWN and ev.key == K_ESCAPE):
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        with _lock:
            w, x, y, z          = _quat
            roll, pitch, yaw    = _angles

        model = _quat_to_mat4(w, x, y, z)
        mvp   = proj @ view @ model   # row-major; will be transposed on upload

        mvp_f = mvp.flatten()
        mod_f = model.flatten()

        # ── Mesh pass ────────────────────────────────────────────────────────
        glUseProgram(prog_mesh)
        glUniformMatrix4fv(glGetUniformLocation(prog_mesh, 'u_mvp'),   1, GL_TRUE, mvp_f)
        glUniformMatrix4fv(glGetUniformLocation(prog_mesh, 'u_model'), 1, GL_TRUE, mod_f)
        glUniform3fv(glGetUniformLocation(prog_mesh, 'u_light'), 1, light)
        glUniform3fv(glGetUniformLocation(prog_mesh, 'u_eye'),   1, eye_pos)

        def draw_mesh(vao, count, prim, color):
            glUniform3fv(glGetUniformLocation(prog_mesh, 'u_color'), 1, color)
            glBindVertexArray(vao)
            glDrawArrays(prim, 0, count)

        draw_mesh(vao_body,  cnt_body,  GL_TRIANGLE_STRIP, STEEL)
        draw_mesh(vao_back,  cnt_back,  GL_TRIANGLE_FAN,   CAP)
        draw_mesh(vao_front, cnt_front, GL_TRIANGLE_FAN,   CAP)
        draw_mesh(vao_ring,  cnt_ring,  GL_TRIANGLE_STRIP, CUTTER)

        glUniform3fv(glGetUniformLocation(prog_mesh, 'u_color'), 1, SPOKE)
        glBindVertexArray(vao_spk)
        glDrawElements(GL_TRIANGLES, cnt_spk, GL_UNSIGNED_INT, None)

        glBindVertexArray(0)

        # ── Axis lines ───────────────────────────────────────────────────────
        glUseProgram(prog_line)
        glUniformMatrix4fv(glGetUniformLocation(prog_line, 'u_mvp'), 1, GL_TRUE, mvp_f)
        glBindVertexArray(vao_axis)
        glLineWidth(2.0)
        glDrawArrays(GL_LINES, 0, cnt_axis)
        glBindVertexArray(0)

        # ── 2D HUD ───────────────────────────────────────────────────────────
        glDisable(GL_DEPTH_TEST)

        # Static: title
        _draw_label(prog_text, ortho, tex_title, W//2 - tw_t//2, H - th_t - 8, tw_t, th_t)

        # Dynamic: R/P/Y values
        for i, (label, val, col) in enumerate([
            (f"Roll   {roll:+7.1f}\u00b0", roll,  (255, 210, 80)),
            (f"Pitch  {pitch:+7.1f}\u00b0", pitch, (80, 230, 130)),
            (f"Yaw    {yaw:+7.1f}\u00b0",   yaw,   (80, 190, 255)),
        ]):
            surf = font_val.render(label, True, col)
            tex, tw, th = _surf_to_tex(surf)
            _draw_label(prog_text, ortho, tex, 12, H - th_t - 22 - (i+1)*36, tw, th)
            glDeleteTextures(1, [tex])

        # Static: hint
        _draw_label(prog_text, ortho, tex_hint, 12, 8, tw_h, th_h)

        glEnable(GL_DEPTH_TEST)

        pygame.display.flip()
        clock.tick(60)

    glDeleteTextures(1, [tex_title])
    glDeleteTextures(1, [tex_hint])
    pygame.quit()

if __name__ == '__main__':
    main()
