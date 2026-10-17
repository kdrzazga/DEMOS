import math
import os
import sys

import pygame
from pygame.locals import K_SPACE
from OpenGL.GLU import gluLookAt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.historical_earth import HistoricalEarth
from lib.test.earth_test import EarthTest


class HistoricalEarthTest(EarthTest):
    """Camera holds still near the globe while it spins the marked cities past; SPACE flips the map's year."""

    def __init__(self, cities, camera_distance=19.0, camera_elevation=30.0, spin_speed=12.0):
        super().__init__(earth_class=HistoricalEarth, caption="Historical Earth Test")
        self.camera_distance = camera_distance
        self.camera_elevation = camera_elevation
        self.earth.spin_speed = spin_speed
        self.earth.moon_enabled = False
        for city, height_share in cities:
            self.earth.mark_city(city, height=self.earth.sign_size * height_share)
        self._show_caption()

    def _show_caption(self):
        pygame.display.set_caption(f"Historical Earth Test - {self.earth.year} (SPACE switches year)")

    def _on_key(self, key):
        if key == K_SPACE:
            years = self.earth.years
            self.earth.show_year(years[(years.index(self.earth.year) + 1) % len(years)])
            self._show_caption()

    def _look_at_earth(self):
        elevation = math.radians(self.camera_elevation)
        gluLookAt(0.0, math.sin(elevation) * self.camera_distance, math.cos(elevation) * self.camera_distance,
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)


def main():
    # Auschwitz stands just south of Lodz, in front of it as seen from the south, so its sign is kept low.
    HistoricalEarthTest((("Lodz", 1.0), ("Auschwitz", 0.55), ("Bergen-Belsen", 1.0),
                         ("New York", 1.0), ("Toronto", 1.0), ("Monte Sereno", 1.0))).run()


if __name__ == "__main__":
    main()
