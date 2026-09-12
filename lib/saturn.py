import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.particles import Texture2D
from lib.moon import Moon


class Saturn:
    def __init__(self, x, y, z, radius=6.0, tilt=26.7, spin_speed=6.0, seed=11,
                 texture_width=1024, texture_height=512, flattening=0.90,
                 moon_size_boost=1.0, moon_orbit_compression=1.0, moon_orbit_scale=0.32,
                 moon_time_scale=0.38, defer_texture=False):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.tilt = tilt
        self.spin_speed = spin_speed
        self.seed = seed
        self.texture_width = texture_width
        self.texture_height = texture_height
        self.flattening = flattening
        self.spin = 0.0

        self.band_palette = ((0.52, 0.40, 0.24), (0.74, 0.62, 0.40), (0.88, 0.80, 0.60),
                             (0.80, 0.70, 0.46), (0.92, 0.86, 0.70))
        self.hex_apothem = 12.0
        self.hex_edge_width = 1.5
        self.hex_inner_color = (0.40, 0.45, 0.47)
        self.hex_edge_color = (0.27, 0.31, 0.35)
        self.vortex_color = (0.22, 0.27, 0.31)

        self.ring_inner = 1.24
        self.ring_outer = 2.34
        self.ring_warm = (0.80, 0.72, 0.55)
        self.ring_cool = (0.66, 0.64, 0.61)

        self.saturn_radius_km = 60268.0
        self.moon_size_boost = moon_size_boost
        self.moon_orbit_compression = moon_orbit_compression
        self.moon_orbit_scale = moon_orbit_scale
        self.moon_time_scale = moon_time_scale
        self.moon_data = (("Titan", 2575.0, 1221870.0, 15.945, 0.35, (0.80, 0.56, 0.24), 40.0),
                          ("Rhea", 764.0, 527108.0, 4.518, 0.33, (0.74, 0.74, 0.72), 215.0))

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        gluQuadricTexture(self.quadric, GL_TRUE)
        self.surface = None
        if not defer_texture:
            self.attach_surface(self._build_surface())
        self.ring_list = self._build_rings()
        self.moons = self._build_moons()

    def update(self, dt):
        self.spin += self.spin_speed * dt
        for moon in self.moons:
            moon.update(dt)

    def attach_surface(self, rgba):
        self.surface = Texture2D(rgba)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)

    def ready(self):
        return self.surface is not None

    def _build_moons(self):
        moons = []
        for name, moon_km, orbit_km, period_days, inclination, color, phase in self.moon_data:
            size = (moon_km / self.saturn_radius_km) * self.radius * self.moon_size_boost
            span = (orbit_km / self.saturn_radius_km) ** self.moon_orbit_compression
            orbit = span * self.moon_orbit_scale * self.radius
            speed = (360.0 / period_days) * self.moon_time_scale
            moons.append(Moon(name, size, orbit, speed, inclination=inclination, color=color, phase=phase))
        return moons

    def _upsample(self, grid, height, width):
        rows = np.linspace(0.0, grid.shape[0] - 1.0, height)
        cols = np.linspace(0.0, grid.shape[1] - 1.0, width)
        row_low = np.floor(rows).astype(int)
        row_high = np.minimum(row_low + 1, grid.shape[0] - 1)
        col_low = np.floor(cols).astype(int)
        col_high = np.minimum(col_low + 1, grid.shape[1] - 1)
        row_frac = (rows - row_low)[:, None]
        col_frac = (cols - col_low)[None, :]
        top = grid[row_low][:, col_low] * (1.0 - col_frac) + grid[row_low][:, col_high] * col_frac
        bottom = grid[row_high][:, col_low] * (1.0 - col_frac) + grid[row_high][:, col_high] * col_frac
        return top * (1.0 - row_frac) + bottom * row_frac

    def _zonal_noise(self, height, width, rng, octaves=5):
        total = np.zeros((height, width), dtype=np.float32)
        amplitude = 1.0
        rows = 12
        cols = 3
        for _ in range(octaves):
            grid = rng.random((rows, cols)).astype(np.float32)
            total += self._upsample(grid, height, width) * amplitude
            amplitude *= 0.55
            rows *= 2
            cols *= 2
        total -= total.mean()
        return total / (np.abs(total).max() + 1e-6)

    def _palette(self, value):
        stops = np.array(self.band_palette, dtype=np.float32)
        scaled = np.clip(value, 0.0, 1.0) * (len(stops) - 1)
        low = np.floor(scaled).astype(int)
        high = np.minimum(low + 1, len(stops) - 1)
        blend = (scaled - low)[:, :, None]
        return stops[low] * (1.0 - blend) + stops[high] * blend

    def _build_surface(self):
        width = self.texture_width
        height = self.texture_height
        rng = np.random.default_rng(self.seed)
        longitude, latitude = np.meshgrid(np.linspace(-180.0, 180.0, width, endpoint=False),
                                          np.linspace(-90.0, 90.0, height))

        bands = (0.55 * np.sin(np.radians(latitude) * 8.0)
                 + 0.30 * np.sin(np.radians(latitude) * 17.0 + 1.1)
                 + 0.16 * np.sin(np.radians(latitude) * 31.0 + 0.4)
                 + 0.10 * np.sin(np.radians(latitude) * 53.0 + 2.2))
        bands = bands + self._zonal_noise(height, width, rng) * 0.45
        bands = bands * (1.0 - 0.35 * np.clip(np.abs(latitude) / 90.0, 0.0, 1.0))
        image = self._palette(bands * 0.5 + 0.5)

        polar_distance = 90.0 - latitude
        sector = ((np.radians(longitude) + math.pi / 6.0) % (math.pi / 3.0)) - math.pi / 6.0
        hex_edge = self.hex_apothem / np.cos(sector)
        hex_edge = hex_edge * (1.0 + self._zonal_noise(height, width, rng, octaves=3) * 0.04)

        inside = np.clip((hex_edge - polar_distance) / 2.0, 0.0, 1.0)
        image = image + (np.array(self.hex_inner_color, dtype=np.float32) - image) * (inside * 0.55)[:, :, None]

        rim = np.clip(1.0 - np.abs(polar_distance - hex_edge) / self.hex_edge_width, 0.0, 1.0)
        image = image + (np.array(self.hex_edge_color, dtype=np.float32) - image) * (rim * 0.85)[:, :, None]

        vortex = np.clip(1.0 - polar_distance / 2.5, 0.0, 1.0)
        image = image + (np.array(self.vortex_color, dtype=np.float32) - image) * (vortex * 0.9)[:, :, None]

        rgba = np.ones((height, width, 4), dtype=np.float32)
        rgba[:, :, :3] = np.clip(image, 0.0, 1.0)
        return rgba * 255.0

    def _ring_density(self, radius):
        density = np.zeros_like(radius)
        density = np.where((radius >= 1.24) & (radius < 1.53), 0.26, density)
        density = np.where((radius >= 1.53) & (radius < 1.72), 0.92, density)
        density = np.where((radius >= 1.72) & (radius < 1.95), 0.78, density)
        density = np.where((radius >= 1.95) & (radius < 2.02), 0.06, density)
        density = np.where((radius >= 2.02) & (radius < 2.21), 0.62, density)
        density = np.where((radius >= 2.21) & (radius < 2.23), 0.09, density)
        density = np.where((radius >= 2.23) & (radius < 2.27), 0.54, density)
        density = np.where((radius >= 2.31) & (radius < 2.33), 0.30, density)
        ripple = 0.86 + 0.14 * np.sin(radius * 95.0)
        return np.clip(density * ripple, 0.0, 1.0)

    def _ring_color(self, radius, density):
        warm = np.array(self.ring_warm, dtype=np.float32)
        cool = np.array(self.ring_cool, dtype=np.float32)
        blend = np.clip((radius - self.ring_inner) / (self.ring_outer - self.ring_inner), 0.0, 1.0)
        tint = warm + (cool - warm) * blend[:, None]
        return tint * (0.55 + 0.45 * density)[:, None]

    def _build_rings(self, radial_steps=110, segments=128):
        radii = np.linspace(self.ring_inner, self.ring_outer, radial_steps)
        density = self._ring_density(radii)
        colors = self._ring_color(radii, density)
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        for index in range(radial_steps - 1):
            glBegin(GL_QUAD_STRIP)
            for step in range(segments + 1):
                angle = math.tau * step / segments
                across = math.cos(angle)
                along = math.sin(angle)
                for edge in (index + 1, index):
                    span = radii[edge] * self.radius
                    glColor4f(colors[edge][0], colors[edge][1], colors[edge][2], density[edge])
                    glVertex3f(across * span, 0.0, along * span)
            glEnd()
        glEndList()
        return display_list

    def _draw_rings(self):
        glDisable(GL_LIGHTING)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCallList(self.ring_list)
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)

    def draw(self):
        if self.surface is None:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.tilt, 0.0, 0.0, 1.0)
        glPushMatrix()
        glRotatef(self.spin, 0.0, 1.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glScalef(1.0, 1.0, self.flattening)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(self.quadric, self.radius, 56, 40)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        for moon in self.moons:
            moon.draw()
        self._draw_rings()
        glPopMatrix()
