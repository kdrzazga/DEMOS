import math

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *


class ScreenTexture:
    def __init__(self, surface):
        self.width, self.height = surface.get_size()
        pixels = pygame.image.tobytes(surface, "RGBA", False)
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, pixels)


class ScreenOverlay:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def begin(self):
        glViewport(0, 0, self.screen_width, self.screen_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.screen_width, self.screen_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def end(self):
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def draw_centered(self, texture, alpha, vertical_share):
        left = (self.screen_width - texture.width) / 2.0
        top = self.screen_height * vertical_share - texture.height / 2.0
        right = left + texture.width
        bottom = top + texture.height
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture.texture_id)
        glColor4f(1.0, 1.0, 1.0, alpha)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(left, top)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(right, top)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(right, bottom)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(left, bottom)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def darken(self, alpha):
        if alpha <= 0.0:
            return
        glColor4f(0.0, 0.0, 0.0, min(alpha, 1.0))
        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(self.screen_width, 0.0)
        glVertex2f(self.screen_width, self.screen_height)
        glVertex2f(0.0, self.screen_height)
        glEnd()


class WelcomeText:
    def __init__(self):
        self.title_font = pygame.font.SysFont("arial", 110, bold=True)
        self.subtitle_font = pygame.font.SysFont("arial", 36)
        self.title_color = (255, 236, 200)
        self.subtitle_color = (190, 200, 230)
        self.title = ScreenTexture(self.title_font.render(
            "WELCOME", True, self.title_color))
        self.subtitle = ScreenTexture(self.subtitle_font.render(
            "from a single pixel to a head", True, self.subtitle_color))
        self.alpha = 0.0

    def draw(self, overlay):
        if self.alpha <= 0.0:
            return
        overlay.draw_centered(self.title, self.alpha, 0.42)
        overlay.draw_centered(self.subtitle, self.alpha, 0.58)


class StageCamera:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.field_of_view = 45.0
        self.distance = 6.5
        self.tilt = 20.0
        self.target_tilt = 20.0
        self.tilt_follow_rate = 1.5
        self.focus_height = 0.0

    def distance_to_fill(self, height, fill_share):
        view_height_per_distance = 2.0 * math.tan(
            math.radians(self.field_of_view / 2.0))
        return height / fill_share / view_height_per_distance

    def update(self, seconds):
        follow = min(self.tilt_follow_rate * seconds, 1.0)
        self.tilt += (self.target_tilt - self.tilt) * follow

    def apply(self):
        glViewport(0, 0, self.screen_width, self.screen_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.screen_width / self.screen_height
        gluPerspective(self.field_of_view, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.distance)
        glRotatef(self.tilt, 1.0, 0.0, 0.0)
        glTranslatef(0.0, -self.focus_height, 0.0)


class Pose:
    def __init__(self):
        self.turn_degrees = 0.0
        self.lift = 0.0
        self.scale = 1.0
        self.upright_degrees = 0.0

    def apply(self):
        glRotatef(self.turn_degrees, 0.0, 1.0, 0.0)
        glTranslatef(0.0, self.lift, 0.0)
        glScalef(self.scale, self.scale, self.scale)
        glRotatef(self.upright_degrees, 1.0, 0.0, 0.0)

    def transform_point(self, point):
        x, y, z = point
        upright = math.radians(self.upright_degrees)
        upright_y = y * math.cos(upright) - z * math.sin(upright)
        upright_z = y * math.sin(upright) + z * math.cos(upright)
        scaled = (x * self.scale, upright_y * self.scale + self.lift,
                  upright_z * self.scale)
        turn = math.radians(self.turn_degrees)
        turned_x = (scaled[0] * math.cos(turn)
                    + scaled[2] * math.sin(turn))
        turned_z = (-scaled[0] * math.sin(turn)
                    + scaled[2] * math.cos(turn))
        return (turned_x, scaled[1], turned_z)
