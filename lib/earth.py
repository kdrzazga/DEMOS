import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.particles import Texture2D
from lib.moon import EarthMoon
from lib.urban.city import CityEntranceSign


class Earth:
    def __init__(self, x, y, z, radius=6.0, tilt=23.4, spin_speed=3.0, texture_path=None,
                 moon_size_boost=1.0, moon_orbit_scale=1.0, moon_time_scale=1.0,
                 moon_enabled=True, places=None, sign_scale=0.1):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.tilt = tilt
        self.spin_speed = spin_speed
        self.spin = 0.0
        self.texture_path = texture_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources", "earth_texture.png")

        self.halo_color = (0.32, 0.56, 0.95)
        self.halo_scale = 1.38

        self.earth_radius_km = 6371.0
        self.moon_enabled = moon_enabled
        self.moon_size_boost = moon_size_boost
        self.moon_orbit_scale = moon_orbit_scale
        self.moon_time_scale = moon_time_scale
        self.moon_data = (("Moon", 1737.4, 384400.0, 27.322, 5.145, (0.62, 0.60, 0.57), 35.0),)

        self.places = dict(places or {})
        self.sign_size = radius * sign_scale
        self.city_signs = {}
        self.sign_sites = {}
        self.nudge_step_degrees = 0.5
        self.max_nudge_degrees = 8.0
        self.nudge_directions = 16

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        gluQuadricTexture(self.quadric, GL_TRUE)
        self.surface = self._load_surface()
        self.halo = Texture2D(self._build_halo())
        self.moons = self._build_moons()

    def update(self, dt):
        self.spin += self.spin_speed * dt
        for moon in self.moons:
            moon.update(dt)

    def _build_moons(self):
        moons = []
        for name, moon_km, orbit_km, period_days, inclination, color, phase in self.moon_data:
            size = (moon_km / self.earth_radius_km) * self.radius * self.moon_size_boost
            orbit = (orbit_km / self.earth_radius_km) * self.radius * self.moon_orbit_scale
            speed = (360.0 / period_days) * self.moon_time_scale
            moons.append(EarthMoon(name, size, orbit, speed, inclination=inclination, color=color, phase=phase))
        return moons

    def _surface_pixels(self):
        image = pygame.image.load(self.texture_path)
        raw = pygame.image.tobytes(image, "RGBA", True)
        return np.frombuffer(raw, dtype=np.uint8).reshape(image.get_height(), image.get_width(), 4)

    def _load_surface(self, pixels=None):
        texture = Texture2D(self._surface_pixels() if pixels is None else pixels)
        glBindTexture(GL_TEXTURE_2D, texture.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        return texture

    def _build_halo(self, size=192):
        axis = (np.arange(size) - (size - 1) / 2.0) / (size / 2.0)
        grid_x, grid_y = np.meshgrid(axis, axis)
        distance = np.sqrt(grid_x * grid_x + grid_y * grid_y)
        alpha = np.exp(-6.5 * np.clip(distance - 0.22, 0.0, None) ** 2)
        alpha[distance > 1.0] = 0.0
        rgba = np.ones((size, size, 4), dtype=np.float32)
        rgba[:, :, 0] = self.halo_color[0]
        rgba[:, :, 1] = self.halo_color[1]
        rgba[:, :, 2] = self.halo_color[2]
        rgba[:, :, 3] = alpha
        return rgba * 255.0

    def _billboard_basis(self):
        view = glGetFloatv(GL_MODELVIEW_MATRIX)
        return ((view[0][0], view[1][0], view[2][0]),
                (view[0][1], view[1][1], view[2][1]))

    def _draw_halo(self):
        right, up = self._billboard_basis()
        reach = self.radius * self.halo_scale
        glDisable(GL_LIGHTING)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.halo.id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        corners = ((0.0, 0.0, -1.0, -1.0), (1.0, 0.0, 1.0, -1.0),
                   (1.0, 1.0, 1.0, 1.0), (0.0, 1.0, -1.0, 1.0))
        glBegin(GL_QUADS)
        for texture_u, texture_v, side, lift in corners:
            glTexCoord2f(texture_u, texture_v)
            glVertex3f(right[0] * side * reach + up[0] * lift * reach,
                       right[1] * side * reach + up[1] * lift * reach,
                       right[2] * side * reach + up[2] * lift * reach)
        glEnd()
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)

    def mark_city(self, name: str, nesw="S", height=None):
        if name not in self.places:
            raise KeyError(f"Unknown place {name!r}; known places: {', '.join(sorted(self.places))}")
        latitude, longitude = self.places[name]
        self.mark_location(name, latitude, longitude, nesw, height)

    def mark_location(self, name: str, latitude, longitude, nesw="S", height=None):
        """height is where the board's top sits above the ground; None means a full sign_size tall sign.

        A sign never stands in water: if its footprint is wet it is nudged to the nearest dry ground.
        """
        sign = CityEntranceSign(name, self.sign_size, nesw, height=height)
        self.sign_sites[name] = (latitude, longitude)
        self.city_signs[name] = (sign, self._surface_placement(*self._dry_ground(sign, latitude, longitude)))

    def unmark_city(self, name: str):
        self.city_signs.pop(name, None)
        self.sign_sites.pop(name, None)

    def _replant_signs(self):
        """Stand every sign again at its requested site, so it dodges the water of the current surface."""
        for name, (sign, _) in self.city_signs.items():
            latitude, longitude = self.sign_sites[name]
            self.city_signs[name] = (sign, self._surface_placement(*self._dry_ground(sign, latitude, longitude)))

    def _is_water(self, latitude, longitude):
        """The plain texture has no reliable land mask, so every spot counts as ground."""
        return False

    def _ground_point(self, latitude, longitude, east_units, south_units):
        north_degrees = -np.degrees(south_units / self.radius)
        east_degrees = np.degrees(east_units / (self.radius * max(np.cos(np.radians(latitude)), 1e-3)))
        return latitude + north_degrees, longitude + east_degrees

    def _nudges(self):
        yield 0.0, 0.0
        steps = int(self.max_nudge_degrees / self.nudge_step_degrees)
        for step in range(1, steps + 1):
            reach = step * self.nudge_step_degrees
            for direction in range(self.nudge_directions):
                angle = 2.0 * np.pi * direction / self.nudge_directions
                yield reach * np.cos(angle), reach * np.sin(angle)

    def _dry_ground(self, sign, latitude, longitude):
        footprint = sign.ground_footprint()
        for north, east in self._nudges():
            spot_latitude, spot_longitude = latitude + north, longitude + east
            if not any(self._is_water(*self._ground_point(spot_latitude, spot_longitude, east_units, south_units))
                       for east_units, south_units in footprint):
                return spot_latitude, spot_longitude
        return latitude, longitude

    def _surface_placement(self, latitude, longitude):
        """Column-major matrix standing a sign on the sphere: x east, y up from the ground, z south.

        In gluSphere's own frame (before draw's -90 degree turn) texture u = (longitude + 180) / 360
        and v runs south to north along z, so the ground point is (cos lat sin lon, -cos lat cos lon, sin lat).
        """
        lat, lon = np.radians(latitude), np.radians(longitude)
        up = np.array((np.cos(lat) * np.sin(lon), -np.cos(lat) * np.cos(lon), np.sin(lat)))
        east = np.array((np.cos(lon), np.sin(lon), 0.0))
        south = np.cross(east, up)
        ground = up * self.radius
        return np.array((*east, 0.0, *up, 0.0, *south, 0.0, *ground, 1.0), dtype=np.float32)

    def _draw_city_signs(self):
        for sign, placement in self.city_signs.values():
            glPushMatrix()
            glMultMatrixf(placement)
            sign.draw()
            glPopMatrix()

    def _draw_surface(self):
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(self.quadric, self.radius, 48, 32)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        self._draw_halo()
        glPushMatrix()
        glRotatef(self.tilt, 0.0, 0.0, 1.0)
        glRotatef(self.spin, 0.0, 1.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        self._draw_surface()
        glDisable(GL_TEXTURE_2D)
        self._draw_city_signs()
        glPopMatrix()
        if self.moon_enabled:
            for moon in self.moons:
                moon.draw()
        glPopMatrix()
