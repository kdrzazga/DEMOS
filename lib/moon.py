import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.particles import Texture2D


class Moon:
    def __init__(self, name, radius, orbit_radius, angular_speed, inclination=0.0,
                 color=(0.74, 0.74, 0.72), phase=0.0, slices=18, stacks=14):
        self.name = name
        self.radius = radius
        self.orbit_radius = orbit_radius
        self.angular_speed = angular_speed
        self.inclination = inclination
        self.color = color
        self.angle = phase
        self.slices = slices
        self.stacks = stacks
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)

    def update(self, dt):
        self.angle += self.angular_speed * dt

    def draw(self):
        glPushMatrix()
        glRotatef(self.inclination, 0.0, 0.0, 1.0)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glTranslatef(self.orbit_radius, 0.0, 0.0)
        glColor3f(*self.color)
        gluSphere(self.quadric, self.radius, self.slices, self.stacks)
        glPopMatrix()


class EarthMoon(Moon):
    """Earth's Moon: a Moon with the lunar surface texture wrapped around the sphere."""

    def __init__(self, name, radius, orbit_radius, angular_speed, inclination=0.0,
                 color=(0.74, 0.74, 0.72), phase=0.0, slices=48, stacks=32, texture_path=None):
        super().__init__(name, radius, orbit_radius, angular_speed, inclination=inclination,
                         color=color, phase=phase, slices=slices, stacks=stacks)
        self.texture_path = texture_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources", "moon.png")
        gluQuadricTexture(self.quadric, GL_TRUE)
        self.surface = self._load_surface()

    def _load_surface(self):
        image = pygame.image.load(self.texture_path)
        raw = pygame.image.tobytes(image, "RGBA", True)
        pixels = np.frombuffer(raw, dtype=np.uint8).reshape(image.get_height(), image.get_width(), 4)
        texture = Texture2D(pixels)
        glBindTexture(GL_TEXTURE_2D, texture.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        return texture

    def draw(self):
        glPushMatrix()
        glRotatef(self.inclination, 0.0, 0.0, 1.0)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glTranslatef(self.orbit_radius, 0.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor3f(1.0, 1.0, 1.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluSphere(self.quadric, self.radius, self.slices, self.stacks)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()
