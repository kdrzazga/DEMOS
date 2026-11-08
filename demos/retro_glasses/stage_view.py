import math

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from lib.globals import Constants
from lib.speech_lines import speech_surface


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
        self.draw_at(texture, alpha, left, top)

    def draw_at(self, texture, alpha, left, top):
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


class SpeechSubtitles:
    def __init__(self):
        self.font = pygame.font.Font(Constants.FONT_PATH, 30)
        self.color = (255, 255, 255)
        self.edge_margin_share = 0.03
        self.vertical_share = 0.82
        self.texture = None

    def show(self, lines):
        self.hide()
        self.texture = ScreenTexture(speech_surface(self.font, lines, self.color))

    def hide(self):
        if self.texture is not None:
            glDeleteTextures([self.texture.texture_id])
            self.texture = None

    def draw(self, overlay):
        if self.texture is None:
            return
        margin = overlay.screen_width * self.edge_margin_share
        left = max(overlay.screen_width - margin - self.texture.width, margin)
        top = overlay.screen_height * self.vertical_share - self.texture.height / 2.0
        overlay.draw_at(self.texture, 1.0, left, top)


class WelcomeText:
    def __init__(self):
        self.title_font = pygame.font.SysFont("arial", 110, bold=True)
        self.subtitle_font = pygame.font.SysFont("arial", 36)
        self.title_color = (255, 236, 200)
        self.subtitle_color = (190, 200, 230)
        self.title = ScreenTexture(self.title_font.render(
            "RETRO GLASSES", True, self.title_color))
        self.subtitle = ScreenTexture(self.subtitle_font.render(
            "Retro computers VS Open GL", True, self.subtitle_color))
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
        self.focus_point = (0.0, 0.0, 0.0)

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
        focus_x, focus_y, focus_z = self.focus_point
        glTranslatef(-focus_x, -focus_y, -focus_z)


class Pose:
    def __init__(self):
        self.turn_degrees = 0.0
        self.lift = 0.0
        self.scale = 1.0
        self.upright_degrees = 0.0
        self.orbit_degrees = 0.0
        self.orbit_center_z = 0.0

    def apply(self):
        glTranslatef(0.0, 0.0, self.orbit_center_z)
        glRotatef(self.orbit_degrees, 0.0, 1.0, 0.0)
        glTranslatef(0.0, 0.0, -self.orbit_center_z)
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
        turned_x, turned_z = self.rotate_around_up(
            scaled[0], scaled[2], self.turn_degrees)
        orbit_x, orbit_z = self.rotate_around_up(
            turned_x, turned_z - self.orbit_center_z, self.orbit_degrees)
        return (orbit_x, scaled[1], orbit_z + self.orbit_center_z)

    def rotate_around_up(self, x, z, degrees):
        angle = math.radians(degrees)
        return (x * math.cos(angle) + z * math.sin(angle),
                -x * math.sin(angle) + z * math.cos(angle))
