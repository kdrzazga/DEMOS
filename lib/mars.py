import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.particles import Texture2D


class Mars:
    def __init__(self, x, y, z, radius=6.0, tilt=25.19, spin_speed=5.0, seed=17,
                 texture_width=1024, texture_height=512, flattening=0.994, defer_texture=False):
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

        self.dust_palette = ((0.50, 0.32, 0.20), (0.64, 0.42, 0.25), (0.72, 0.50, 0.31),
                             (0.79, 0.58, 0.38), (0.86, 0.69, 0.49))
        self.dark_region_color = (0.38, 0.29, 0.23)
        self.bright_dust_color = (0.88, 0.72, 0.52)
        self.canyon_color = (0.30, 0.21, 0.16)
        self.caldera_color = (0.34, 0.24, 0.18)
        self.ice_color = (0.94, 0.95, 0.96)

        self.dark_regions = ((70.0, 10.0, 13.0, 14.0, 1.00), (-25.0, 45.0, 26.0, 16.0, 0.70),
                             (-42.0, -24.0, 24.0, 12.0, 0.85), (-150.0, -28.0, 28.0, 11.0, 0.85),
                             (145.0, -24.0, 30.0, 12.0, 0.80), (-8.0, -8.0, 22.0, 6.0, 0.90),
                             (115.0, 45.0, 26.0, 14.0, 0.55), (95.0, -20.0, 18.0, 10.0, 0.75),
                             (-88.0, -26.0, 9.0, 7.0, 0.90))
        self.bright_regions = ((70.0, -42.0, 19.0, 14.0, 1.00), (20.0, 22.0, 24.0, 18.0, 0.60),
                               (-105.0, 2.0, 26.0, 22.0, 0.50), (147.0, 25.0, 16.0, 13.0, 0.50),
                               (-160.0, 20.0, 22.0, 16.0, 0.45))
        self.volcanoes = ((-133.0, 18.0, 4.5), (-104.0, 12.0, 2.5),
                          (-113.0, 0.0, 2.3), (-121.0, -9.0, 2.6))
        self.canyon = (-60.0, -10.0, 32.0, 2.6, 0.06)
        self.north_cap = 78.0
        self.south_cap = -74.0
        self.crater_count = 45

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        gluQuadricTexture(self.quadric, GL_TRUE)
        self.surface = None
        if not defer_texture:
            self.attach_surface(self._build_surface())

    def update(self, dt):
        self.spin += self.spin_speed * dt

    def attach_surface(self, rgba):
        self.surface = Texture2D(rgba)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)

    def ready(self):
        return self.surface is not None

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

    def _noise(self, height, width, rng, octaves=5, cells=3):
        total = np.zeros((height, width), dtype=np.float32)
        amplitude = 1.0
        for _ in range(octaves):
            grid = rng.random((cells, cells * 2)).astype(np.float32)
            total += self._upsample(grid, height, width) * amplitude
            amplitude *= 0.54
            cells *= 2
        total -= total.mean()
        return total / (np.abs(total).max() + 1e-6)

    def _blob(self, longitude, latitude, center_lon, center_lat, span_lon, span_lat):
        delta_lon = (longitude - center_lon + 180.0) % 360.0 - 180.0
        distance = (delta_lon / span_lon) ** 2 + ((latitude - center_lat) / span_lat) ** 2
        return np.clip(1.0 - distance, 0.0, 1.0)

    def _palette(self, value):
        stops = np.array(self.dust_palette, dtype=np.float32)
        scaled = np.clip(value, 0.0, 1.0) * (len(stops) - 1)
        low = np.floor(scaled).astype(int)
        high = np.minimum(low + 1, len(stops) - 1)
        blend = (scaled - low)[:, :, None]
        return stops[low] * (1.0 - blend) + stops[high] * blend

    def _craters(self, longitude, latitude, rng):
        field = np.zeros(longitude.shape, dtype=np.float32)
        for _ in range(self.crater_count):
            center_lat = math.degrees(math.asin(rng.uniform(-0.98, 0.98)))
            center_lon = rng.uniform(-180.0, 180.0)
            span = rng.uniform(1.3, 5.5)
            squeeze = max(0.15, math.cos(math.radians(center_lat)))
            delta_lon = (longitude - center_lon + 180.0) % 360.0 - 180.0
            distance = np.sqrt((delta_lon * squeeze / span) ** 2 + ((latitude - center_lat) / span) ** 2)
            field += np.clip(1.0 - np.abs(distance - 1.0) * 3.0, 0.0, 1.0) * 0.30
            field -= np.clip(1.0 - distance, 0.0, 1.0) * 0.40
        return np.clip(field, -1.0, 1.0)

    def _build_surface(self):
        width = self.texture_width
        height = self.texture_height
        rng = np.random.default_rng(self.seed)
        longitude, latitude = np.meshgrid(np.linspace(-180.0, 180.0, width, endpoint=False),
                                          np.linspace(-90.0, 90.0, height))

        dust = self._noise(height, width, rng, octaves=6) * 0.5 + 0.5
        dust = np.clip(dust + self._noise(height, width, rng, octaves=3, cells=2) * 0.18, 0.0, 1.0)
        image = self._palette(dust)

        edge_noise = self._noise(height, width, rng, octaves=4)
        dark = np.zeros((height, width), dtype=np.float32)
        for center_lon, center_lat, span_lon, span_lat, strength in self.dark_regions:
            dark = np.maximum(dark, self._blob(longitude, latitude, center_lon, center_lat,
                                               span_lon, span_lat) * strength)
        dark = np.clip(dark * (1.0 + edge_noise * 0.55) - 0.05, 0.0, 1.0)
        image = image + (np.array(self.dark_region_color, dtype=np.float32) - image) * (dark * 0.80)[:, :, None]

        bright = np.zeros((height, width), dtype=np.float32)
        for center_lon, center_lat, span_lon, span_lat, strength in self.bright_regions:
            bright = np.maximum(bright, self._blob(longitude, latitude, center_lon, center_lat,
                                                   span_lon, span_lat) * strength)
        bright = np.clip(bright * (1.0 + edge_noise * 0.35), 0.0, 1.0)
        image = image + (np.array(self.bright_dust_color, dtype=np.float32) - image) * (bright * 0.55)[:, :, None]

        crater = self._craters(longitude, latitude, rng)
        image = np.clip(image * (1.0 + crater[:, :, None] * 0.22), 0.0, 1.0)

        canyon_lon, canyon_lat, canyon_span, canyon_width, canyon_slope = self.canyon
        delta_lon = (longitude - canyon_lon + 180.0) % 360.0 - 180.0
        drift = canyon_lat + delta_lon * canyon_slope
        gash = np.clip(1.0 - ((delta_lon / canyon_span) ** 2 + ((latitude - drift) / canyon_width) ** 2), 0.0, 1.0)
        gash = gash * (1.0 + edge_noise * 0.30)
        image = image + (np.array(self.canyon_color, dtype=np.float32) - image) * np.clip(gash * 0.85, 0.0, 1.0)[:, :, None]

        for center_lon, center_lat, span in self.volcanoes:
            squeeze = max(0.2, math.cos(math.radians(center_lat)))
            flank = self._blob(longitude, latitude, center_lon, center_lat, span / squeeze, span)
            image = image + (np.array(self.bright_dust_color, dtype=np.float32) - image) * (flank * 0.40)[:, :, None]
            caldera = self._blob(longitude, latitude, center_lon, center_lat, span * 0.30 / squeeze, span * 0.30)
            image = image + (np.array(self.caldera_color, dtype=np.float32) - image) * (caldera * 0.80)[:, :, None]

        cap_noise = self._noise(height, width, rng, octaves=4) * 4.0
        north = np.clip((latitude - (self.north_cap + cap_noise)) / 4.0, 0.0, 1.0)
        south = np.clip(((self.south_cap + cap_noise) - latitude) / 4.0, 0.0, 1.0)
        frost = np.clip(north + south, 0.0, 1.0)
        image = image + (np.array(self.ice_color, dtype=np.float32) - image) * frost[:, :, None]

        rgba = np.ones((height, width, 4), dtype=np.float32)
        rgba[:, :, :3] = np.clip(image, 0.0, 1.0)
        return rgba * 255.0

    def draw(self):
        if self.surface is None:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.tilt, 0.0, 0.0, 1.0)
        glRotatef(self.spin, 0.0, 1.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glScalef(1.0, 1.0, self.flattening)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(self.quadric, self.radius, 48, 32)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
