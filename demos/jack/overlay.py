import os

import numpy as np
import pygame
from OpenGL.GL import *

from lib.particles import Texture2D
from lib.typer import FONT_PATH

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res")


def resource(file_name):
    return os.path.join(RESOURCES, file_name)


class ScreenOverlay:
    def __init__(self, width, height, photo_box_shares=(0.14, 0.07, 0.72, 0.72)):
        self.width = width
        self.height = height
        self.photo_box_shares = photo_box_shares

    def apply(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.width, self.height, 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

    def finish(self):
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def photo_box(self):
        left, top, width, height = self.photo_box_shares
        return left * self.width, top * self.height, width * self.width, height * self.height

    def whole_screen(self):
        return 0.0, 0.0, float(self.width), float(self.height)

    @staticmethod
    def fit(aspect, box):
        box_x, box_y, box_width, box_height = box
        width = min(box_width, box_height * aspect)
        height = width / aspect
        return box_x + (box_width - width) / 2.0, box_y + (box_height - height) / 2.0, width, height

    def cover(self, aspect):
        width = max(self.width, self.height * aspect)
        height = width / aspect
        return (self.width - width) / 2.0, (self.height - height) / 2.0, width, height

    def draw_texture(self, texture_id, rectangle, alpha=1.0, tint=(1.0, 1.0, 1.0)):
        x, y, width, height = rectangle
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor4f(*tint, alpha)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(x, y)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(x + width, y)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(x + width, y + height)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(x, y + height)
        glEnd()

    def draw_rectangle(self, rectangle, color, alpha):
        x, y, width, height = rectangle
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color, alpha)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()
        glEnable(GL_TEXTURE_2D)

    def darken(self, opacity):
        if opacity > 0.0:
            self.draw_rectangle(self.whole_screen(), (0.0, 0.0, 0.0), min(1.0, opacity))


class SurfaceSprite:
    def __init__(self):
        self.texture = None
        self.width = 0
        self.height = 0

    def upload(self, surface):
        if self.texture is not None:
            glDeleteTextures([self.texture.id])
        self.width, self.height = surface.get_size()
        raw = pygame.image.tobytes(surface, "RGBA", False)
        self.texture = Texture2D(np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 4))

    def draw(self, overlay, x, y, alpha=1.0):
        if self.texture is not None and alpha > 0.0:
            overlay.draw_texture(self.texture.id, (x, y, self.width, self.height), alpha)


class ScreenText(SurfaceSprite):
    def __init__(self, size, font_path=FONT_PATH, color=(255, 255, 255), shadow_color=(0, 0, 0), shadow_offset=3):
        super().__init__()
        self.font = pygame.font.Font(font_path, size)
        self.color = color
        self.shadow_color = shadow_color
        self.shadow_offset = shadow_offset
        self.text = None

    def set_text(self, text):
        if text == self.text:
            return
        self.text = text
        glyphs = self.font.render(text, True, self.color)
        shadow = self.font.render(text, True, self.shadow_color)
        surface = pygame.Surface((glyphs.get_width() + self.shadow_offset, glyphs.get_height() + self.shadow_offset),
                                 pygame.SRCALPHA)
        surface.blit(shadow, (self.shadow_offset, self.shadow_offset))
        surface.blit(glyphs, (0, 0))
        self.upload(surface)


class YearLabel:
    def __init__(self, screen_height, size_share=0.045, margin_share=0.04, fade_seconds=0.5):
        self.text = ScreenText(int(screen_height * size_share))
        self.margin = int(screen_height * margin_share)
        self.fade_seconds = fade_seconds
        self.wanted = None
        self.shown = None
        self.alpha = 0.0

    def show(self, label):
        self.wanted = label

    def update(self, dt):
        settled = self.shown == self.wanted
        target = 1.0 if settled and self.shown else 0.0
        step = dt / self.fade_seconds
        self.alpha = min(target, self.alpha + step) if target > self.alpha else max(target, self.alpha - step)
        if not settled and self.alpha <= 0.0:
            self.shown = self.wanted
            if self.shown:
                self.text.set_text(self.shown)

    def draw(self, overlay):
        if self.shown:
            self.text.draw(overlay, self.margin, overlay.height - self.margin - self.text.height, self.alpha)
