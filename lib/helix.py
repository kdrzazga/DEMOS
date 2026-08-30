import colorsys
import random
import math

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants


class HelixItem:

    def __init__(self, texture, color, angle, initial_y, speed, radius,
                 axis_x, axis_z, top_limit, bottom_limit, half_width, half_height):
        self.texture = texture
        self.color = color
        self.angle = angle
        self.initial_y = initial_y
        self.y = initial_y
        self.speed = speed * (1 + random.uniform(0.01, 0.05))
        self.radius = radius
        self.axis_x = axis_x * (1 + random.uniform(0.01, 0.05))
        self.axis_z = axis_z * (1 + random.uniform(0.01, 0.15))
        self.top_limit = top_limit
        self.bottom_limit = bottom_limit
        self.half_width = half_width
        self.half_height = half_height

    def update(self):
        self.y += self.speed
        if self.speed >= 0:
            if self.y > self.top_limit:
                self.reset()
        elif self.y < self.bottom_limit:
            self.reset()

    def spin(self):
        self.angle += math.pi / 60

    def reset(self):
        self.y = self.initial_y


class Helix:

    def __init__(self, x, speed, content, count=300, radius=0.35, pitch=0.006,
                 angle_step=math.pi / 10, z_axis=0.0, item_half_height=0.05,
                 fov=Constants.FOV, camera_z=Constants.CAMERA_Z, far_plane=300.0,
                 margin=0.1, z_stretch=1.0, x_flatten=1.0):
        self.fov = fov
        self.camera_z = camera_z
        self.far_plane = far_plane
        self.z_stretch = z_stretch
        self.x_flatten = x_flatten

        texture, content_width, content_height = self._build_texture(content)
        half_height = item_half_height
        half_width = item_half_height * content_width / content_height

        eye_distance = -camera_z - z_axis
        visible_half_height = eye_distance * math.tan(math.radians(fov / 2))
        top_limit = visible_half_height * (1 + 2 * margin)
        bottom_limit = -top_limit

        self.items = []
        for i in range(count):
            angle = i * angle_step
            if speed >= 0:
                initial_y = bottom_limit - i * pitch
            else:
                initial_y = top_limit + i * pitch
            color = colorsys.hsv_to_rgb(i / count, 1.0, 1.0)
            self.items.append(HelixItem(
                texture, color, angle, initial_y, speed, radius,
                x, z_axis, top_limit, bottom_limit, half_width, half_height))

    def update(self):
        for item in self.items:
            item.update()
            item.spin()

    def draw(self):
        width, height = pygame.display.get_surface().get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width / height, 0.1, self.far_plane)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.camera_z)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        for item in sorted(self.items, key=self._item_z):
            item_x = self.x_flatten * (item.axis_x + item.radius * math.cos(item.angle))
            item_z = self._item_z(item)
            left = item_x - item.half_width
            right = item_x + item.half_width
            top = item.y + item.half_height
            bottom = item.y - item.half_height
            glColor3f(*item.color)
            glBindTexture(GL_TEXTURE_2D, item.texture)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(left, top, item_z)
            glTexCoord2f(1, 0); glVertex3f(right, top, item_z)
            glTexCoord2f(1, 1); glVertex3f(right, bottom, item_z)
            glTexCoord2f(0, 1); glVertex3f(left, bottom, item_z)
            glEnd()
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    def _item_z(self, item):
        return item.axis_z + self.z_stretch * item.radius * math.sin(item.angle)

    def _build_texture(self, content):
        if isinstance(content, pygame.Surface):
            surface = content
        elif isinstance(content, str):
            surface = pygame.image.load(content).convert_alpha()
        else:
            width, height = content.size()
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            content.render(surface, transparent_space=True)
        data = pygame.image.tobytes(surface, "RGBA")
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(),
                     surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture, surface.get_width(), surface.get_height()


class PetsciiHelix(Helix):

    def _build_texture(self, content):
        rows = len(content.chars)
        columns = len(content.chars[0])
        cell_width, cell_height = content.font(content.char_size).size("W")
        surface = pygame.Surface((columns * cell_width, rows * cell_height), pygame.SRCALPHA)
        for row in range(rows):
            for column in range(columns):
                if not content.is_blank(row, column):
                    content.draw_cell(surface, content.char_size, (cell_width, cell_height), row, column)
        data = pygame.image.tobytes(surface, "RGBA")
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(),
                     surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture, surface.get_width(), surface.get_height()
