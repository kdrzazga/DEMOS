import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from demos.retro_glasses.models3d.lesson13_head import Head
from demos.retro_glasses.models3d.lesson14_sunglasses import Sunglasses


class SunglassesTestApp:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.background = (0.05, 0.05, 0.08, 1.0)
        self.field_of_view = 45.0
        self.camera_distance = 3.0
        self.closest_distance = 1.0
        self.farthest_distance = 15.0
        self.zoom_step = 0.2
        self.tilt_degrees = 20.0
        self.turn_degrees = 0.0
        self.spin_degrees_per_second = 30.0
        self.spinning = True
        self.drag_degrees_per_pixel = 0.4
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        pygame.display.set_caption(
            "Sunglasses test   [drag rotate, wheel zoom, SPACE spin, ESC quit]")
        glEnable(GL_DEPTH_TEST)
        self.head = Head()
        self.sunglasses = Sunglasses(self.head)
        self.sunglasses_center = numpy.mean(
            [outline.center for outline in self.sunglasses.outlines], axis=0)
        self.clock = pygame.time.Clock()
        self.dragging = False
        self.running = True

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.spinning = not self.spinning

    def zoom(self, wheel_steps):
        distance = self.camera_distance - wheel_steps * self.zoom_step
        self.camera_distance = min(max(distance, self.closest_distance), self.farthest_distance)

    def drag(self, relative_motion):
        moved_x, moved_y = relative_motion
        self.turn_degrees += moved_x * self.drag_degrees_per_pixel
        self.tilt_degrees += moved_y * self.drag_degrees_per_pixel

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEWHEEL:
                self.zoom(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.drag(event.rel)

    def update(self, seconds):
        if self.spinning and not self.dragging:
            self.turn_degrees += self.spin_degrees_per_second * seconds

    def apply_camera(self):
        window_width, window_height = self.window_size
        glViewport(0, 0, window_width, window_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, window_width / window_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glRotatef(self.tilt_degrees, 1.0, 0.0, 0.0)
        glRotatef(self.turn_degrees, 0.0, 1.0, 0.0)

    def draw_sunglasses(self):
        glPushMatrix()
        glScalef(self.head.scale, self.head.scale, self.head.scale)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        glTranslatef(*(-self.sunglasses_center))
        glEnable(GL_NORMALIZE)
        self.sunglasses.draw()
        glDisable(GL_NORMALIZE)
        glPopMatrix()

    def draw(self):
        glClearColor(*self.background)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.apply_camera()
        self.draw_sunglasses()

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.update(seconds)
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    SunglassesTestApp().run()
