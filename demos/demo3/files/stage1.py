import math
import os
import random

import pygame
from OpenGL.GL import *

from demos.demo3.files.base_stage import BaseStage


class _Card:
    """One tossed picture: a position, an outward velocity, and its own spin
    about a random axis. When it flies out of bounds it is respawned back at the
    burst origin with a fresh random direction, so the fountain never empties."""

    def __init__(self, spawn):
        self._spawn = spawn
        self.pos = [0.0, 0.0, 0.0]
        self.vel = [0.0, 0.0, 0.0]
        self.axis = (0.0, 1.0, 0.0)
        self.angle = 0.0
        self.spin = 0.0
        self.respawn()

    def respawn(self):
        self.pos = [random.uniform(-0.2, 0.2) for _ in range(3)]
        dx, dy, dz = self._random_direction()
        speed = random.uniform(*self._spawn.speed_range)
        self.vel = [dx * speed, dy * speed, dz * speed]
        self.axis = self._random_direction()
        self.angle = random.uniform(0.0, 360.0)
        self.spin = random.uniform(*self._spawn.spin_range)

    def update(self, gravity, bound):
        self.vel[1] -= gravity
        for i in range(3):
            self.pos[i] += self.vel[i]
        self.angle += self.spin
        if self.pos[1] < -bound or self._distance2() > bound * bound:
            self.respawn()

    def _distance2(self):
        return sum(c * c for c in self.pos)

    @staticmethod
    def _random_direction():
        z = random.uniform(-1.0, 1.0)
        phi = random.uniform(0.0, 2.0 * math.pi)
        r = math.sqrt(max(0.0, 1.0 - z * z))
        return (r * math.cos(phi), r * math.sin(phi), z)


class Stage1(BaseStage):
    """A 3D burst of 64 keyboard pictures flung in every direction, each card
    tumbling about its own axis, with the whole swarm slowly orbited by the
    camera. Fades in from black so the cut from the intro movie is seamless."""

    def __init__(self, win_w, win_h, res_path, fov):
        super().__init__(win_w, win_h, res_path, fov)

        # --- tunables (kept as instance config, not class-level state) --------
        self.picture = "keyb.png"
        self.count = 64
        self.cam_z = -6.0            # push the swarm back from the camera
        self.gravity = 0.0009        # gentle downward pull -> tossed arcs
        self.bound = 9.0             # respawn once a card flies past this radius
        self.speed_range = (0.03, 0.085)
        self.spin_range = (1.4, 4.2)
        self.card_half_w = 0.6
        self.yaw_speed = 0.35        # degrees/frame of slow camera orbit
        self.fade_frames = 30        # black -> scene fade-in
        self.background = (0.02, 0.02, 0.05)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        self.texture, aspect = self._load_texture(os.path.join(res_path, self.picture))
        self.card_half_h = self.card_half_w / aspect
        self.cards = [_Card(self) for _ in range(self.count)]

    def _load_texture(self, path):
        surface = pygame.image.load(path)
        w, h = surface.get_width(), surface.get_height()
        tex = self.make_texture()
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(surface, "RGBA", True))
        return tex, w / h

    def render(self):
        glClearColor(*self.background, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.cam_z)
        glRotatef(self.frame * self.yaw_speed, 0.0, 1.0, 0.0)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        for card in self.cards:
            card.update(self.gravity, self.bound)
            self._draw_card(card)
        glDisable(GL_TEXTURE_2D)

        fade = 1.0 - min(1.0, self.frame / self.fade_frames)
        if fade > 0.0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.fill_screen(0.0, 0.0, 0.0, fade)
            glDisable(GL_BLEND)

        self.frame += 1

    def _draw_card(self, card):
        hw, hh = self.card_half_w, self.card_half_h
        glPushMatrix()
        glTranslatef(*card.pos)
        glRotatef(card.angle, *card.axis)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex3f(-hw, -hh, 0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f(hw, -hh, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f(hw, hh, 0.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-hw, hh, 0.0)
        glEnd()
        glPopMatrix()

    def destroy(self):
        glDeleteTextures([self.texture])
