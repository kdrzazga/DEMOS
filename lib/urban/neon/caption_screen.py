import os

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_LIGHTING,
    GL_LINEAR,
    GL_ONE,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor4f,
    glDepthMask,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glPopAttrib,
    glPushAttrib,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTexSubImage2D,
    glVertex3f,
)


class TickerTape:

    def __init__(self, font_path, font_size, height, tube_color):
        self.font_path = font_path
        self.font_size = font_size
        self.height = height
        self.tube_color = tube_color
        self.core_color = tuple(min(255, channel + (255 - channel) * 3 // 5) for channel in tube_color)
        self.background = (8, 10, 12)
        self.glow_radius = 6
        self.glow_passes = 2
        self.spacer = "     "
        self.surface = None

    def paint(self, text):
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.Font(self.font_path, self.font_size)
        words = text + self.spacer
        width = font.size(words)[0]
        tape = pygame.Surface((width, self.height))
        tape.fill(self.background)
        baseline = (self.height - font.get_height()) // 2
        lettering = font.render(words, True, self.tube_color, (0, 0, 0))
        tube = pygame.Surface(lettering.get_size())
        tube.blit(lettering, (0, 0))
        glow = pygame.transform.gaussian_blur(tube, self.glow_radius)
        for _ in range(self.glow_passes):
            tape.blit(glow, (0, baseline), special_flags=pygame.BLEND_ADD)
        tape.blit(font.render(words, True, self.core_color), (0, baseline))
        self.surface = tape
        return tape

    @property
    def width(self):
        return self.surface.get_width()


class CaptionScreen:

    def __init__(self, face, across, rise, width, height, text, tube_color):
        self.wall_offset = 0.45
        self.corners = (face.point(across, rise, self.wall_offset),
                        face.point(across + width, rise, self.wall_offset),
                        face.point(across + width, rise + height, self.wall_offset),
                        face.point(across, rise + height, self.wall_offset))
        self.facing = face.normal
        self.text = text
        self.pixel_width = 512
        self.pixel_height = 64
        self.scroll_speed = 70.0
        self.frame_color = tube_color
        self.frame_thickness = 3
        self.scanline_spacing = 3
        self.scanline_shade = (0, 0, 0, 70)
        self.glow_spread = (1.08, 1.9)
        self.glow_strength = 0.4
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                 "resources", "Mx437_ACM_VGA_8x16.ttf")
        self.tape = TickerTape(font_path, 52, self.pixel_height, tube_color)
        self.offset = 0.0
        self.shown_offset = None
        self.texture_id = None
        self.scanlines = None

    def prepare(self):
        self.tape.paint(self.text)
        self.scanlines = self._paint_scanlines()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.pixel_width, self.pixel_height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     self._frame_pixels(0))
        self.shown_offset = 0

    def set_text(self, text):
        self.text = text
        self.tape.paint(text)
        self.offset = 0.0
        self.shown_offset = None

    def update(self, seconds):
        self.offset = (self.offset + self.scroll_speed * seconds) % self.tape.width
        whole_offset = int(self.offset)
        if whole_offset != self.shown_offset:
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.pixel_width, self.pixel_height, GL_RGBA, GL_UNSIGNED_BYTE,
                            self._frame_pixels(whole_offset))
            self.shown_offset = whole_offset

    def _paint_scanlines(self):
        overlay = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        for y in range(0, self.pixel_height, self.scanline_spacing):
            pygame.draw.line(overlay, self.scanline_shade, (0, y), (self.pixel_width, y))
        return overlay

    def _frame_pixels(self, whole_offset):
        frame = pygame.Surface((self.pixel_width, self.pixel_height))
        x = -whole_offset
        while x < self.pixel_width:
            frame.blit(self.tape.surface, (x, 0))
            x += self.tape.width
        frame.blit(self.scanlines, (0, 0))
        pygame.draw.rect(frame, self.frame_color, frame.get_rect(), self.frame_thickness)
        return pygame.image.tobytes(frame, "RGBA", True)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        self._quad(self.corners)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(1.0, 1.0, 1.0, self.glow_strength)
        self._quad(self._glow_corners())
        glPopAttrib()

    def _glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5 + self.facing * 0.05
        half_across = (bottom_right - bottom_left) * (0.5 * self.glow_spread[0])
        half_up = (top_left - bottom_left) * (0.5 * self.glow_spread[1])
        return (center - half_across - half_up, center + half_across - half_up,
                center + half_across + half_up, center - half_across + half_up)

    def _quad(self, corners):
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(corners, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
            glTexCoord2f(u, v)
            glVertex3f(*corner)
        glEnd()
