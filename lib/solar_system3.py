import math

from OpenGL.GL import *

from lib.earth import Earth
from lib.mars import Mars
from lib.saturn import Saturn


class SolarSystem3:
    def __init__(self, x=0.0, y=0.0, z=0.0, planet_scale=1.0, orbit_scale=95.0,
                 year_seconds=20.0, light=GL_LIGHT0, light_color=(1.0, 0.97, 0.90),
                 moon_orbit_scale=0.08):
        self.x = x
        self.y = y
        self.z = z
        self.planet_scale = planet_scale
        self.orbit_scale = orbit_scale
        self.year_seconds = year_seconds
        self.light = light
        self.light_color = light_color
        self.moon_orbit_scale = moon_orbit_scale
        self.earth_radius_km = 6378.0
        self.bodies = self._build_bodies()

    def _speed(self, period_years):
        return 360.0 / (period_years * self.year_seconds)

    def _size(self, radius_km):
        return (radius_km / self.earth_radius_km) * self.planet_scale

    def _build_bodies(self):
        earth = Earth(0.0, 0.0, 0.0, radius=self._size(6378.0),
                      moon_orbit_scale=self.moon_orbit_scale)
        mars = Mars(0.0, 0.0, 0.0, radius=self._size(3396.0))
        saturn = Saturn(0.0, 0.0, 0.0, radius=self._size(60268.0))
        return [[earth, 1.0000 * self.orbit_scale, self._speed(1.0000), 0.000, 20.0],
                [mars, 1.5237 * self.orbit_scale, self._speed(1.8808), 1.850, 140.0],
                [saturn, 9.5826 * self.orbit_scale, self._speed(29.457), 2.485, 250.0]]

    def planets(self):
        return [body[0] for body in self.bodies]

    def update(self, dt):
        for body in self.bodies:
            body[4] += body[2] * dt
            planet, orbit, speed, inclination, angle = body
            sweep = math.radians(angle)
            lean = math.radians(inclination)
            flat_x = math.cos(sweep) * orbit
            flat_z = math.sin(sweep) * orbit
            planet.x = self.x + flat_x
            planet.y = self.y - flat_z * math.sin(lean)
            planet.z = self.z + flat_z * math.cos(lean)
            planet.update(dt)

    def _apply_light(self):
        glEnable(self.light)
        glLightfv(self.light, GL_POSITION, (self.x, self.y, self.z, 1.0))
        glLightfv(self.light, GL_DIFFUSE, (self.light_color[0], self.light_color[1],
                                           self.light_color[2], 1.0))
        glLightfv(self.light, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(self.light, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(self.light, GL_LINEAR_ATTENUATION, 0.0)
        glLightf(self.light, GL_QUADRATIC_ATTENUATION, 0.0)

    def draw(self):
        self._apply_light()
        for body in self.bodies:
            body[0].draw()
