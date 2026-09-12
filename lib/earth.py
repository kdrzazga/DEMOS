import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.particles import Texture2D
from lib.moon import Moon


class Earth:
    def __init__(self, x, y, z, radius=6.0, tilt=23.4, spin_speed=3.0, texture_path=None,
                 moon_size_boost=1.0, moon_orbit_scale=1.0, moon_time_scale=1.0):
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
        self.moon_size_boost = moon_size_boost
        self.moon_orbit_scale = moon_orbit_scale
        self.moon_time_scale = moon_time_scale
        self.moon_data = (("Moon", 1737.4, 384400.0, 27.322, 5.145, (0.62, 0.60, 0.57), 35.0),)

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
            moons.append(Moon(name, size, orbit, speed, inclination=inclination, color=color, phase=phase))
        return moons

    def _load_surface(self):
        image = pygame.image.load(self.texture_path)
        raw = pygame.image.tobytes(image, "RGBA", True)
        pixels = np.frombuffer(raw, dtype=np.uint8).reshape(image.get_height(), image.get_width(), 4)
        texture = Texture2D(pixels)
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

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        self._draw_halo()
        glPushMatrix()
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor3f(1.0, 1.0, 1.0)
        glRotatef(self.tilt, 0.0, 0.0, 1.0)
        glRotatef(self.spin, 0.0, 1.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluSphere(self.quadric, self.radius, 48, 32)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        for moon in self.moons:
            moon.draw()
        glPopMatrix()
