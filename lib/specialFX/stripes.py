import colorsys
import math
import random
from OpenGL.GL import *


class StripeEffects:
    """Horizontal stripe effects drawn as flat, unlit GL quads over a picture laid out in pixels.

    A picture is placed by the world position of its top-left pixel (corner) and the world size of one
    pixel (pixel_size); pixel rows grow downwards, the stripes face +z.
    blue_interference() uses the picture placed with place_picture() and the time advanced by update().
    """

    def __init__(self, seed=3):
        self.seed = seed
        self.random = random.Random(seed)
        self.interference_streak_count = 80
        self.interference_streak_thickness = (3, 10)
        self.interference_shade_range = (0.3, 1.0)
        self.corner = (0.0, 0.0, 0.0)
        self.pixel_size = 1.0
        self.time = 0.0
        self.blue_color = (0.612, 0.522, 0.980)
        self.blue_height_share = (0.1, 0.25)
        self.blue_blink_period = 1.0
        self.blue_blink_duration = 0.3
        self.blue_travel_period = 4.0

    def place_picture(self, corner, pixel_size):
        self.corner = corner
        self.pixel_size = pixel_size

    def update(self, delta_seconds):
        self.time += delta_seconds

    def interference(self, corner, pixel_size, picture_width, bands, brightness=0.3, shading_color=None,
                     transparency=0.0):
        """Draws interference_streak_count streaks across the whole picture width, each within a random band.

        bands are (top, height) pairs in pixels, or (top, height, shading_color) to override shading_color
        within that band. Without a shading color a streak gets a random, fully saturated hue; with an
        (r, g, b) shading color it is that color darkened by a random factor from interference_shade_range.
        transparency runs from 0.0 (opaque streaks) to 1.0 (invisible streaks).
        """
        left, top, front = corner
        self._draw_streaks(left, left + picture_width * pixel_size, top, front, pixel_size, bands,
                           self.interference_streak_count, brightness, shading_color, transparency)

    def blue_interference(self, x, y, width, height, stripes_count, brightness=1.0, transparency=0.0):
        """Draws stripes_count blue-shaded streaks in a band blinking within the area (x, y, width, height),
        in pixels of the placed picture.

        The band shows for blue_blink_duration every blue_blink_period seconds, gets a random height
        from blue_height_share of the area height at every blink and travels up and down the area
        once every blue_travel_period seconds.
        """
        if self.time % self.blue_blink_period >= self.blue_blink_duration:
            return
        blink_number = int(self.time // self.blue_blink_period)
        band_height = round(height * random.Random(self.seed * 1000003 + blink_number).uniform(*self.blue_height_share))
        travel_share = 0.5 - 0.5 * math.cos(2.0 * math.pi * self.time / self.blue_travel_period)
        band_top = y + round((height - band_height) * travel_share)
        corner_left, top, front = self.corner
        left = corner_left + x * self.pixel_size
        self._draw_streaks(left, left + width * self.pixel_size, top, front, self.pixel_size,
                           [(band_top, band_height)], stripes_count, brightness, self.blue_color, transparency)

    def _draw_streaks(self, left, right, top, front, pixel_size, bands, streak_count, brightness, shading_color,
                      transparency):
        if not bands:
            return
        opacity = 1.0 - transparency
        blend_was_enabled = glIsEnabled(GL_BLEND)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_QUADS)
        for _ in range(streak_count):
            band = self.random.choice(bands)
            streak_top, streak_bottom = self._random_streak(band)
            band_shading_color = band[2] if len(band) > 2 else shading_color
            glColor4f(*self._streak_color(brightness, band_shading_color), opacity)
            glVertex3f(left, top - streak_bottom * pixel_size, front)
            glVertex3f(right, top - streak_bottom * pixel_size, front)
            glVertex3f(right, top - streak_top * pixel_size, front)
            glVertex3f(left, top - streak_top * pixel_size, front)
        glEnd()
        if not blend_was_enabled:
            glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _random_streak(self, band):
        """A streak (top, bottom) in pixels within the band."""
        band_top, band_height = band[:2]
        thickness = min(self.random.randint(*self.interference_streak_thickness), band_height)
        streak_top = band_top + self.random.randint(0, band_height - thickness)
        return streak_top, streak_top + thickness

    def _streak_color(self, brightness, shading_color):
        if shading_color is None:
            return colorsys.hsv_to_rgb(self.random.random(), 1.0, brightness)
        shade = self.random.uniform(*self.interference_shade_range) * brightness
        return tuple(channel * shade for channel in shading_color)
