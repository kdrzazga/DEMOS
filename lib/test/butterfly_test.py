import copy
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.animals.butterfly import Butterfly2D, Butterfly3D, WingPattern
from lib.butterfly_credits import ButterflyCredits


class CreditsOverlay:
    def __init__(self, window_size):
        self.window_size = window_size
        self.screen_fraction = 0.75
        self.panel_size = (round(window_size[0] * self.screen_fraction), round(window_size[1] * self.screen_fraction))
        self.panel_left = (window_size[0] - self.panel_size[0]) // 2
        self.panel_top = (window_size[1] - self.panel_size[1]) // 2
        self.panel_surface = pygame.Surface(self.panel_size, pygame.SRCALPHA)
        self.credits = ButterflyCredits(0, 0, *self.panel_size)
        self.credits.butterflies.speed_factor = 2.0
        self.texture = None

    def update(self, delta_seconds):
        self.credits.update(delta_seconds)

    def upload_panel(self):
        if self.texture is None:
            self.texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        pixels = pygame.image.tobytes(self.panel_surface, "RGBA", True)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *self.panel_size, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)

    def draw(self):
        self.panel_surface.fill((0, 0, 0, 0))
        self.credits.draw(self.panel_surface)
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT)
        self.upload_panel()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.window_size[0], self.window_size[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_ALPHA_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        left, top = self.panel_left, self.panel_top
        right, bottom = left + self.panel_size[0], top + self.panel_size[1]
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(left, top)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(right, top)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(right, bottom)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(left, bottom)
        glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class Butterfly2DScene:
    def __init__(self, window_size, pattern):
        self.screen = pygame.display.set_mode(window_size)
        self.background_color = (150, 190, 140)
        self.large_butterfly = Butterfly2D(520)
        self.large_center = (420, 360)
        self.small_butterflies = [Butterfly2D(170) for _ in range(4)]
        self.small_centers = [(900, 200), (1130, 200), (900, 500), (1130, 500)]
        self.small_hue_offsets = [0.0, 90.0, 180.0, 270.0]
        self.small_flap_frequencies = [2.0, 2.6, 3.1, 1.7]
        self.minimum_opening = 0.25
        self.elapsed_seconds = 0.0
        self.apply_pattern(pattern)

    def apply_pattern(self, pattern):
        self.large_butterfly.shape.pattern = copy.copy(pattern)
        self.large_butterfly.render()
        for butterfly, hue_offset in zip(self.small_butterflies, self.small_hue_offsets):
            butterfly.shape.pattern = copy.copy(pattern)
            butterfly.shape.pattern.hue += hue_offset
            butterfly.render()

    def handle_event(self, event):
        pass

    def update(self, delta_seconds):
        self.elapsed_seconds += delta_seconds

    def wing_opening(self, frequency):
        swing = abs(math.cos(math.pi * frequency * self.elapsed_seconds))
        return self.minimum_opening + (1.0 - self.minimum_opening) * swing

    def draw(self):
        self.screen.fill(self.background_color)
        self.large_butterfly.draw(self.screen, self.large_center)
        for butterfly, center, frequency in zip(self.small_butterflies, self.small_centers, self.small_flap_frequencies):
            butterfly.draw(self.screen, center, self.wing_opening(frequency))

    def caption(self):
        return "Butterfly2D"


class Butterfly3DScene:
    def __init__(self, window_size, pattern):
        pygame.display.set_mode(window_size, DOUBLEBUF | OPENGL)
        glViewport(0, 0, *window_size)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, window_size[0] / window_size[1], 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        self.background_color = (0.55, 0.72, 0.85)
        self.camera_distance = 6.0
        self.view_pitch_degrees = 25.0
        self.view_yaw_degrees = 30.0
        self.auto_spin_degrees_per_second = 20.0
        self.mouse_degrees_per_pixel = 0.4
        self.frequency_step = 0.25
        self.flapping = True
        self.dragging = False
        self.butterfly = Butterfly3D()
        self.butterfly.orientation_degrees = [-90.0, 0.0, 0.0]
        self.credits_delay_seconds = 2.0
        self.scene_seconds = 0.0
        self.credits_overlay = CreditsOverlay(window_size)
        self.apply_pattern(pattern)

    def apply_pattern(self, pattern):
        self.butterfly.shape.pattern = copy.copy(pattern)
        self.butterfly.rebuild()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.view_yaw_degrees += event.rel[0] * self.mouse_degrees_per_pixel
            self.view_pitch_degrees += event.rel[1] * self.mouse_degrees_per_pixel
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            self.flapping = not self.flapping
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self.butterfly.flap_frequency += self.frequency_step
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            self.butterfly.flap_frequency = max(0.0, self.butterfly.flap_frequency - self.frequency_step)

    def update(self, delta_seconds):
        if not self.dragging:
            self.view_yaw_degrees += self.auto_spin_degrees_per_second * delta_seconds
        if self.flapping:
            self.butterfly.flap_wings(delta_seconds)
        self.scene_seconds += delta_seconds
        if self.credits_visible():
            self.credits_overlay.update(delta_seconds)

    def credits_visible(self):
        return self.scene_seconds >= self.credits_delay_seconds

    def draw(self):
        glClearColor(*self.background_color, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glRotatef(self.view_pitch_degrees, 1.0, 0.0, 0.0)
        glRotatef(self.view_yaw_degrees, 0.0, 1.0, 0.0)
        self.butterfly.draw()
        if self.credits_visible():
            self.credits_overlay.draw()

    def caption(self):
        return f"Butterfly3D - flap {self.butterfly.flap_frequency:.2f} Hz - F flap, UP/DOWN speed, drag to rotate"


class ButterflyTest:
    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.hue_step = 15.0
        self.pattern_toggle_keys = {
            pygame.K_1: "show_bands",
            pygame.K_2: "show_veins",
            pygame.K_3: "show_eyespots",
            pygame.K_4: "show_edge_dots",
        }
        pygame.init()
        self.clock = pygame.time.Clock()
        self.pattern = WingPattern()
        self.scene = Butterfly2DScene(self.window_size, self.pattern)
        self.running = True

    def switch_scene(self):
        if isinstance(self.scene, Butterfly2DScene):
            self.scene = Butterfly3DScene(self.window_size, self.pattern)
        else:
            self.scene = Butterfly2DScene(self.window_size, self.pattern)

    def change_pattern(self, key):
        if key in self.pattern_toggle_keys:
            attribute = self.pattern_toggle_keys[key]
            setattr(self.pattern, attribute, not getattr(self.pattern, attribute))
        elif key == pygame.K_LEFT:
            self.pattern.hue -= self.hue_step
        elif key == pygame.K_RIGHT:
            self.pattern.hue += self.hue_step
        else:
            return
        self.scene.apply_pattern(self.pattern)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.switch_scene()
            elif event.type == pygame.KEYDOWN:
                self.change_pattern(event.key)
                self.scene.handle_event(event)
            else:
                self.scene.handle_event(event)

    def run(self):
        while self.running:
            self.handle_events()
            delta_seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.scene.update(delta_seconds)
            self.scene.draw()
            pygame.display.flip()
            pygame.display.set_caption(f"{self.scene.caption()} - TAB 2D/3D, 1-4 patterns, LEFT/RIGHT hue, ESC quit - {self.clock.get_fps():.0f} fps")
        pygame.quit()


if __name__ == "__main__":
    ButterflyTest().run()
