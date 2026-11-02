import math

import numpy as np

from lib.particles import ParticleBatch


class RoundNebula(ParticleBatch):
    def __init__(self, texture, center=(0.0, 0.0, -80.0), radius=28.0,
                 shell_puffs=1200, haze_puffs=420, core_puffs=12,
                 rim_color=(1.0, 0.42, 0.12), shell_color=(1.0, 0.68, 0.28),
                 inner_color=(0.50, 0.40, 0.85), core_color=(1.0, 0.88, 0.96),
                 spin_speed=0.06, seed=1):
        super().__init__(texture)
        self.center = np.array(center, dtype=np.float32)
        self.radius = float(radius)
        self.spin_speed = float(spin_speed)
        rng = np.random.default_rng(seed)
        comps = (
            self._shell(rng, shell_puffs, rim_color, shell_color),
            self._haze(rng, haze_puffs, inner_color),
            self._core(rng, core_puffs, core_color),
        )
        keys = ("pos", "rgb", "alpha", "size")
        merged = {k: np.concatenate([c[k] for c in comps], axis=0) for k in keys}
        motion_keys = ("sway_amp", "sway_freq", "sway_phase", "pulse_amp", "pulse_freq", "pulse_phase")
        motion = {k: np.concatenate([c["motion"][k] for c in comps], axis=0) for k in motion_keys}
        self._install(merged["pos"], merged["rgb"], merged["alpha"], merged["size"], motion)
        self._rel = np.ascontiguousarray(self.base_pos - self.center)

    def _directions(self, rng, n):
        v = rng.normal(0.0, 1.0, (n, 3))
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-6)

    def _shell(self, rng, n, rim_color, shell_color):
        dirs = self._directions(rng, n)
        knots = 1.0 + rng.normal(0.0, 0.07, n) + (rng.random(n) < 0.16) * rng.uniform(0.06, 0.20, n)
        factor = np.clip(knots, 0.72, 1.34)
        pos = self.center + dirs * (self.radius * factor)[:, None]
        edge = np.clip((factor - 0.9) / 0.44, 0.0, 1.0)
        rim = np.array(rim_color)
        shell = np.array(shell_color)
        rgb = shell + (rim - shell) * edge[:, None]
        rgb = np.clip(rgb + rng.normal(0.0, 0.03, (n, 3)), 0.0, 1.0)
        alpha = rng.uniform(0.10, 0.22, n)
        size = self.radius * rng.uniform(0.05, 0.11, n)
        motion = self._motion(rng, n, (0.05, 0.25), (0.10, 0.40), (0.05, 0.15), (0.20, 0.60))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)

    def _haze(self, rng, n, inner_color):
        dirs = self._directions(rng, n)
        depth = (rng.random(n) ** 0.5) * 0.9
        pos = self.center + dirs * (self.radius * depth)[:, None]
        base = np.array(inner_color)
        rgb = np.clip(base + rng.normal(0.0, 0.04, (n, 3)), 0.0, 1.0)
        alpha = rng.uniform(0.05, 0.12, n)
        size = self.radius * rng.uniform(0.10, 0.20, n)
        motion = self._motion(rng, n, (0.10, 0.35), (0.10, 0.40), (0.08, 0.20), (0.20, 0.60))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)

    def _core(self, rng, n, core_color):
        dirs = self._directions(rng, n)
        pos = self.center + dirs * (self.radius * 0.04 * rng.random(n))[:, None]
        rgb = np.tile(np.array(core_color), (n, 1))
        rgb[rng.random(n) < 0.4] = np.array([1.0, 0.55, 0.85])
        rgb = np.clip(rgb + rng.normal(0.0, 0.02, (n, 3)), 0.0, 1.0)
        alpha = rng.uniform(0.55, 0.95, n)
        size = self.radius * rng.uniform(0.03, 0.06, n)
        motion = self._motion(rng, n, (0.0, 0.0), (0.0, 0.0), (0.10, 0.30), (0.50, 1.50))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)

    def update(self, t):
        angle = t * self.spin_speed
        ca = math.cos(angle)
        sa = math.sin(angle)
        rx = self._rel[:, 0] * ca + self._rel[:, 2] * sa
        rz = -self._rel[:, 0] * sa + self._rel[:, 2] * ca
        rotated = np.column_stack([rx, self._rel[:, 1], rz])
        sway = self.sway_amp * np.sin(self.sway_freq[:, None] * t + self.sway_phase)
        self.positions = np.ascontiguousarray(self.center + rotated + sway)
        pulse = 1.0 + self.pulse_amp * np.sin(self.pulse_freq * t + self.pulse_phase)
        self.colors[:, 3] = np.clip(self.base_alpha * pulse, 0.0, 1.0)
