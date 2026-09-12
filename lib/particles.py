import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt


class Texture2D:
    def __init__(self, rgba):
        data = np.ascontiguousarray(rgba.astype(np.uint8))
        h, w = data.shape[:2]
        self.id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)


class TextureLibrary:
    def __init__(self, glow_size=128, spike_size=192):
        self.glow = Texture2D(self._glow(glow_size))
        self.spike = Texture2D(self._spike(spike_size))

    def _grid(self, size):
        axis = (np.arange(size) - (size - 1) / 2.0) / (size / 2.0)
        dx, dy = np.meshgrid(axis, axis)
        return dx, dy, np.sqrt(dx * dx + dy * dy)

    def _to_rgba(self, alpha):
        alpha = np.clip(alpha, 0.0, 1.0)
        rgba = np.ones((alpha.shape[0], alpha.shape[1], 4), dtype=np.float32)
        rgba[:, :, 3] = alpha
        return rgba * 255.0

    def _glow(self, size):
        _, _, r = self._grid(size)
        alpha = np.exp(-4.6 * r * r)
        alpha[r > 1.0] = 0.0
        return self._to_rgba(alpha)

    def _spike(self, size):
        dx, dy, r = self._grid(size)
        core = np.exp(-7.0 * r * r)
        horiz = np.exp(-(dy * 24.0) ** 2) * np.exp(-(dx * 1.7) ** 2)
        vert = np.exp(-(dx * 24.0) ** 2) * np.exp(-(dy * 1.7) ** 2)
        alpha = core + 0.6 * (horiz + vert)
        return self._to_rgba(alpha)


class BillboardBatch:
    def __init__(self, texture):
        self.texture = texture
        self._quad = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        self._count = 0
        self._texcoords = None
        self.positions = None
        self.colors = None
        self.size = None

    def _build_texcoords(self):
        tile = np.array(self._quad, dtype=np.float32)
        self._texcoords = np.ascontiguousarray(np.tile(tile, (self._count, 1)))

    def render(self, right, up):
        s = self.size[:, None]
        rx = (right * s).astype(np.float32)
        ux = (up * s).astype(np.float32)
        offs = np.empty((self._count, 4, 3), dtype=np.float32)
        offs[:, 0] = -rx - ux
        offs[:, 1] = rx - ux
        offs[:, 2] = rx + ux
        offs[:, 3] = -rx + ux
        verts = np.ascontiguousarray((self.positions[:, None, :] + offs).reshape(-1, 3))
        cols = np.ascontiguousarray(np.repeat(self.colors, 4, axis=0))
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        glVertexPointer(3, GL_FLOAT, 0, verts)
        glColorPointer(4, GL_FLOAT, 0, cols)
        glTexCoordPointer(2, GL_FLOAT, 0, self._texcoords)
        glDrawArrays(GL_QUADS, 0, self._count * 4)


class ParticleBatch(BillboardBatch):
    def __init__(self, texture):
        super().__init__(texture)
        self.base_pos = None
        self.rgb = None
        self.base_alpha = None
        self.sway_amp = None
        self.sway_freq = None
        self.sway_phase = None
        self.pulse_amp = None
        self.pulse_freq = None
        self.pulse_phase = None

    def _motion(self, rng, n, sway, sway_freq, pulse, pulse_freq):
        return dict(
            sway_amp=rng.uniform(sway[0], sway[1], (n, 3)),
            sway_freq=rng.uniform(sway_freq[0], sway_freq[1], n),
            sway_phase=rng.uniform(0.0, math.tau, (n, 3)),
            pulse_amp=rng.uniform(pulse[0], pulse[1], n),
            pulse_freq=rng.uniform(pulse_freq[0], pulse_freq[1], n),
            pulse_phase=rng.uniform(0.0, math.tau, n),
        )

    def _install(self, pos, rgb, alpha, size, motion):
        n = len(pos)
        self._count = n
        self.base_pos = np.ascontiguousarray(pos.astype(np.float32))
        self.rgb = rgb.astype(np.float32)
        self.base_alpha = alpha.astype(np.float32)
        self.size = size.astype(np.float32)
        self.sway_amp = motion["sway_amp"].astype(np.float32)
        self.sway_freq = motion["sway_freq"].astype(np.float32)
        self.sway_phase = motion["sway_phase"].astype(np.float32)
        self.pulse_amp = motion["pulse_amp"].astype(np.float32)
        self.pulse_freq = motion["pulse_freq"].astype(np.float32)
        self.pulse_phase = motion["pulse_phase"].astype(np.float32)
        self.positions = self.base_pos.copy()
        self.colors = np.ones((n, 4), dtype=np.float32)
        self.colors[:, :3] = self.rgb
        self._build_texcoords()

    def update(self, t):
        sway = self.sway_amp * np.sin(self.sway_freq[:, None] * t + self.sway_phase)
        self.positions = np.ascontiguousarray(self.base_pos + sway)
        pulse = 1.0 + self.pulse_amp * np.sin(self.pulse_freq * t + self.pulse_phase)
        self.colors[:, 3] = np.clip(self.base_alpha * pulse, 0.0, 1.0)


class Camera:
    def __init__(self, config):
        self.config = config
        self.distance = float(config.camera_distance)
        self.target = np.array(config.look_at, dtype=np.float32)
        self.up_world = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.eye = np.array([0.0, 0.0, config.camera_distance], dtype=np.float32)
        self.right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    def move_away(self, distance=0.04):
        self.distance += distance

    def update(self, t):
        ox, oy, oz = self.config.orbit
        sx, sy, sz = self.config.orbit_speed
        ex = self.target[0] + ox * math.sin(t * sx)
        ey = self.target[1] + oy * math.sin(t * sy)
        ez = self.target[2] + self.distance + oz * math.sin(t * sz)
        self.eye = np.array([ex, ey, ez], dtype=np.float32)
        forward = self.target - self.eye
        forward = forward / np.linalg.norm(forward)
        right = np.cross(forward, self.up_world)
        right = right / np.linalg.norm(right)
        self.right = right.astype(np.float32)
        self.up = np.cross(right, forward).astype(np.float32)

    def apply(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.eye[0], self.eye[1], self.eye[2],
            self.target[0], self.target[1], self.target[2],
            self.up_world[0], self.up_world[1], self.up_world[2],
        )
