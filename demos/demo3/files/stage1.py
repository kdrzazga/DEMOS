import glob
import math
import os
import random

import pygame
from OpenGL.GL import *

from demos.demo3.files.base_stage import BaseStage


class _Card:
    """One tossed keycap: its own texture, a position, an outward velocity, and
    a spin about a random axis. It is launched once from the burst origin; when
    it crosses the bound it is marked dead and never comes back."""

    def __init__(self, spawn, tex, base_hw, base_hh):
        self._spawn = spawn
        self.tex = tex
        self.dead = False
        self.pos = [random.uniform(-0.25, 0.25) for _ in range(3)]
        dx, dy, dz = self._random_direction()
        speed = random.uniform(*spawn.speed_range)
        self.vel = [dx * speed, dy * speed, dz * speed]
        self.axis = self._random_direction()
        self.angle = random.uniform(0.0, 360.0)
        self.spin = random.uniform(*spawn.spin_range)
        scale = random.uniform(*spawn.scale_range)
        self.hw = base_hw * scale
        self.hh = base_hh * scale

    def update(self, gravity, bound):
        self.vel[1] -= gravity
        for i in range(3):
            self.pos[i] += self.vel[i]
        self.angle += self.spin
        if self.pos[1] < -bound or self._distance2() > bound * bound:
            self.dead = True

    def _distance2(self):
        return sum(c * c for c in self.pos)

    @staticmethod
    def _random_direction():
        z = random.uniform(-1.0, 1.0)
        phi = random.uniform(0.0, 2.0 * math.pi)
        r = math.sqrt(max(0.0, 1.0 - z * z))
        return (r * math.cos(phi), r * math.sin(phi), z)


class Stage1(BaseStage):
    """A single 3D burst of the individual keycaps (cut out into keys/*.png)
    flung in every direction, each card tumbling about its own axis while the
    camera slowly orbits. Each key is launched once and, once it flies past the
    edge, it is gone for good - when the last one leaves, the stage is done. The
    cutouts are drawn with alpha-testing so each card shows the key's real
    silhouette with correct depth (no sorting needed). Fades in from black so
    the cut from the intro movie is seamless."""

    def __init__(self, win_w, win_h, res_path, fov):
        super().__init__(win_w, win_h, res_path, fov)

        # --- tunables (kept as instance config, not class-level state) --------
        self.keys_dir = "keys"
        self.cam_z = -6.0            # push the swarm back from the camera
        self.gravity = 0.0009        # gentle downward pull -> tossed arcs
        self.bound = 9.0             # respawn once a card flies past this radius
        self.speed_range = (0.03, 0.085)
        self.spin_range = (1.4, 4.2)
        self.scale_range = (0.8, 1.25)
        self.key_half = 0.5          # half-size of a key's longest edge, in world units
        self.yaw_speed = 0.35        # degrees/frame of slow camera orbit
        self.fade_frames = 30        # black -> scene fade-in
        self.background = (0.02, 0.02, 0.05)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        self.textures = []
        self.cards = []
        for path in sorted(glob.glob(os.path.join(res_path, self.keys_dir, "*.png"))):
            tex, aspect = self._load_texture(path)
            self.textures.append(tex)
            # normalise by the longer edge so the wide spacebar doesn't dominate
            if aspect >= 1.0:
                base_hw, base_hh = self.key_half, self.key_half / aspect
            else:
                base_hw, base_hh = self.key_half * aspect, self.key_half
            self.cards.append(_Card(self, tex, base_hw, base_hh))
        self.count = len(self.cards)

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
        glEnable(GL_ALPHA_TEST)          # drop the transparent background of each cutout
        glAlphaFunc(GL_GREATER, 0.5)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        for card in self.cards:
            if card.dead:
                continue
            card.update(self.gravity, self.bound)
            self._draw_card(card)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_ALPHA_TEST)

        fade = 1.0 - min(1.0, self.frame / self.fade_frames)
        if fade > 0.0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.fill_screen(0.0, 0.0, 0.0, fade)
            glDisable(GL_BLEND)

        self.frame += 1

    def _draw_card(self, card):
        hw, hh = card.hw, card.hh
        glBindTexture(GL_TEXTURE_2D, card.tex)
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

    @property
    def done(self):
        return bool(self.cards) and all(card.dead for card in self.cards)

    def destroy(self):
        if self.textures:
            glDeleteTextures(self.textures)
