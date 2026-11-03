import math

import numpy as np

from lib.particles import Camera, ParticleBatch


class Config:
    def __init__(self):
        self.width = 1000
        self.height = 800
        self.title = "Eagle Nebula - M16"
        self.fps = 60
        self.fov = 52.0
        self.near = 1.0
        self.far = 1100.0
        self.background = (0.015, 0.02, 0.035, 1.0)
        self.camera_distance = 46.0
        self.look_at = (0.0, -2.0, -6.0)
        self.orbit = (7.5, 3.0, 5.0)
        self.orbit_speed = (0.061, 0.043, 0.031)
        self.move_away_delay = 2.0
        self.background_puffs = 340
        self.stars = 4000
        self.star_volume = (-380.0, 380.0, -320.0, 300.0, -480.0, 760.0)
        self.spike_stars = 16
        self.spike_volume = (-130.0, 130.0, -95.0, 90.0, -400.0, 600.0)
        self.bg_palette = (
            (0.10, 0.34, 0.42),
            (0.09, 0.22, 0.44),
            (0.15, 0.36, 0.32),
            (0.20, 0.16, 0.40),
            (0.12, 0.40, 0.46),
        )
        self.glow_tint = (0.45, 0.60, 0.65)
        self.pillar_core = (0.28, 0.16, 0.09)
        self.pillar_tan = (0.60, 0.40, 0.22)
        self.pillar_gold = (1.00, 0.76, 0.40)
        self.pillar_hot = (1.00, 0.92, 0.72)
        self.light_dir = (0.60, 0.70, 0.35)
        self.star_cool = (0.80, 0.86, 1.00)
        self.star_warm = (1.00, 0.86, 0.66)
        self.star_pure = (1.00, 1.00, 1.00)
        self.spike_colors = (
            (0.85, 0.90, 1.00),
            (1.00, 1.00, 1.00),
            (1.00, 0.85, 0.65),
            (1.00, 0.55, 0.90),
        )
        self.pillars = (
            (-9.0, -14.0, -4.0, 25.0, 4.4, 1.7, 2.6, 0.0, 1.2, 300),
            (2.0, -21.0, -6.0, 31.0, 3.3, 1.2, 1.6, 0.0, 0.6, 320),
            (10.0, -20.0, -2.0, 16.0, 3.0, 1.1, -1.6, 0.0, 0.5, 180),
            (-100.0, -24.0, -55.0, 34.0, 5.0, 1.8, 3.0, 0.0, 1.5, 300),
            (100.0, -26.0, -62.0, 40.0, 5.5, 2.0, -3.5, 0.0, 1.0, 320),
            (-80.0, -52.0, -95.0, 30.0, 4.5, 1.6, 2.5, 0.0, 1.2, 300),
            (120.0, 16.0, -102.0, 36.0, 5.0, 1.8, -3.0, 0.0, 1.2, 320),
        )


class NebulaGas(ParticleBatch):
    def __init__(self, config, texture, seed=7):
        super().__init__(texture)
        rng = np.random.default_rng(seed)
        comps = [self._background(rng, config)]
        for pillar in config.pillars:
            comps.append(self._pillar(rng, config, pillar))
        comps.append(self._tips(rng, config))
        keys = ("pos", "rgb", "alpha", "size")
        merged = {k: np.concatenate([c[k] for c in comps], axis=0) for k in keys}
        motion_keys = ("sway_amp", "sway_freq", "sway_phase", "pulse_amp", "pulse_freq", "pulse_phase")
        motion = {k: np.concatenate([c["motion"][k] for c in comps], axis=0) for k in motion_keys}
        self._install(merged["pos"], merged["rgb"], merged["alpha"], merged["size"], motion)

    def _background(self, rng, config):
        n = config.background_puffs
        x = rng.uniform(-24.0, 24.0, n)
        y = rng.uniform(-22.0, 16.0, n)
        z = rng.uniform(-46.0, -6.0, n)
        pos = np.column_stack([x, y, z])
        palette = np.array(config.bg_palette)
        idx = rng.integers(0, len(palette), n)
        rgb = np.clip(palette[idx] + rng.normal(0.0, 0.03, (n, 3)), 0.0, 1.0)
        size = rng.uniform(5.0, 13.0, n)
        alpha = rng.uniform(0.03, 0.08, n)
        d = np.sqrt(x * x + (y - 3.0) ** 2 + (z + 16.0) ** 2 * 0.15)
        glow = np.clip(1.0 - d / 24.0, 0.0, 1.0)
        alpha = alpha + glow * 0.06
        rgb = np.clip(rgb + glow[:, None] * np.array(config.glow_tint) * 0.30, 0.0, 1.0)
        motion = self._motion(rng, n, (0.3, 0.9), (0.03, 0.15), (0.05, 0.15), (0.08, 0.30))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)

    def _pillar(self, rng, config, pillar):
        bx, by, bz, h, br, tr, cx, cy, cz, n = pillar
        base = np.array([bx, by, bz])
        curve = np.array([cx, cy, cz])
        up = np.array([0.0, 1.0, 0.0])
        u = rng.random(n) ** 0.8
        radius = br + (tr - br) * u
        ang = rng.uniform(0.0, math.tau, n)
        rr = radius * np.sqrt(rng.random(n))
        ox = np.cos(ang) * rr
        oz = np.sin(ang) * rr
        oy = rng.normal(0.0, h * 0.02, n)
        spine = base + up * (h * u)[:, None] + curve * (u ** 1.6)[:, None]
        pos = spine + np.column_stack([ox, oy, oz])
        core = np.array(config.pillar_core)
        tan = np.array(config.pillar_tan)
        gold = np.array(config.pillar_gold)
        hot = np.array(config.pillar_hot)
        rgb = core + (tan - core) * u[:, None]
        lit = np.array(config.light_dir)
        lit = lit / np.linalg.norm(lit)
        off = np.column_stack([ox, np.zeros(n), oz])
        offn = off / (np.linalg.norm(off, axis=1, keepdims=True) + 1e-6)
        rim = np.clip(offn @ lit, 0.0, 1.0) ** 1.6 * (0.35 + 0.65 * u)
        rgb = rgb * (1.0 - 0.6 * rim[:, None]) + gold * rim[:, None] * 0.9
        tip = np.clip((u - 0.72) / 0.28, 0.0, 1.0)
        rgb = np.clip(rgb + hot * (tip * 0.5)[:, None], 0.0, 1.0)
        alpha = np.clip(rng.uniform(0.10, 0.22, n) + rim * 0.12 + tip * 0.18, 0.0, 0.9)
        size = rng.uniform(1.1, 2.7, n) * (1.15 - 0.35 * u)
        motion = self._motion(rng, n, (0.1, 0.5), (0.10, 0.40), (0.05, 0.15), (0.15, 0.50))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)

    def _tips(self, rng, config):
        positions = []
        rgbs = []
        alphas = []
        sizes = []
        for pillar in config.pillars:
            bx, by, bz, h, br, tr, cx, cy, cz, n = pillar
            top = np.array([bx + cx, by + h + cy, bz + cz])
            k = 7
            off = rng.normal(0.0, 1.0, (k, 3)) * np.array([1.3, 1.8, 1.3])
            positions.append(top + off)
            rgbs.append(np.clip(np.array([1.0, 0.90, 0.72]) + rng.normal(0.0, 0.04, (k, 3)), 0.0, 1.0))
            alphas.append(rng.uniform(0.35, 0.70, k))
            sizes.append(rng.uniform(0.7, 1.8, k))
        pos = np.concatenate(positions)
        rgb = np.concatenate(rgbs)
        alpha = np.concatenate(alphas)
        size = np.concatenate(sizes)
        motion = self._motion(rng, len(pos), (0.05, 0.20), (0.10, 0.40), (0.20, 0.50), (0.40, 1.50))
        return dict(pos=pos, rgb=rgb, alpha=alpha, size=size, motion=motion)


class StarField(ParticleBatch):
    def __init__(self, config, texture, seed=19):
        super().__init__(texture)
        rng = np.random.default_rng(seed)
        n = config.stars
        xmin, xmax, ymin, ymax, zmin, zmax = config.star_volume
        x = rng.uniform(xmin, xmax, n)
        y = rng.uniform(ymin, ymax, n)
        z = rng.uniform(zmin, zmax, n)
        pos = np.column_stack([x, y, z])
        pick = rng.random(n)[:, None]
        cool = np.array(config.star_cool)
        warm = np.array(config.star_warm)
        pure = np.array(config.star_pure)
        rgb = np.where(pick < 0.7, cool, np.where(pick < 0.9, pure, warm))
        rgb = np.clip(rgb + rng.normal(0.0, 0.03, (n, 3)), 0.0, 1.0)
        size = rng.uniform(0.28, 0.90, n)
        size = np.where(rng.random(n) < 0.06, size * 3.2, size)
        alpha = rng.uniform(0.5, 1.0, n)
        motion = self._motion(rng, n, (0.0, 0.0), (0.0, 0.0), (0.20, 0.70), (0.5, 3.5))
        self._install(pos, rgb, alpha, size, motion)


class SpikeStars(ParticleBatch):
    def __init__(self, config, texture, seed=23):
        super().__init__(texture)
        rng = np.random.default_rng(seed)
        n = config.spike_stars
        xmin, xmax, ymin, ymax, zmin, zmax = config.spike_volume
        x = rng.uniform(xmin, xmax, n)
        y = rng.uniform(ymin, ymax, n)
        z = rng.uniform(zmin, zmax, n)
        pos = np.column_stack([x, y, z])
        palette = np.array(config.spike_colors)
        rgb = palette[rng.integers(0, len(palette), n)]
        size = rng.uniform(3.0, 6.0, n)
        alpha = rng.uniform(0.7, 1.0, n)
        motion = self._motion(rng, n, (0.0, 0.0), (0.0, 0.0), (0.15, 0.40), (0.30, 1.20))
        self._install(pos, rgb, alpha, size, motion)


class Scene:
    def __init__(self, config, textures):
        self.config = config
        self.camera = Camera(config)
        self.gas = NebulaGas(config, textures.glow)
        self.stars = StarField(config, textures.glow)
        self.spikes = SpikeStars(config, textures.spike)
        self.batches = (self.gas, self.stars, self.spikes)

    def update(self, t):
        self.camera.update(t)
        for batch in self.batches:
            batch.update(t)

    def render(self):
        self.camera.apply()
        for batch in self.batches:
            batch.render(self.camera.right, self.camera.up)
