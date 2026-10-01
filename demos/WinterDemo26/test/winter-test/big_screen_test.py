import os
import sys
import math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_f, K_d, K_t
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from demos.WinterDemo26.big_screen import BigScreen


class BigScreenTest:
    def __init__(self, width=1100, height=700, fade_duration=1.5, dark_level=0.1,
                 resources=os.path.join(os.path.dirname(__file__), "..", "..", "resources"),
                 english_file="wishes1.txt", german_file="wuenschen1.txt", text_size=79):
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.fade_started = 0.0
        self.fade_duration = fade_duration
        self.dark_level = dark_level
        self.english_file = os.path.join(resources, english_file)
        self.german_file = os.path.join(resources, german_file)
        self.text_size = text_size
        self.hall_dark = False
        self.front_view = True
        self.background = (0.07, 0.03, 0.10)
        self.light_diffuse = (0.75, 0.45, 0.95)
        self.light_ambient = (0.22, 0.12, 0.26)
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Big Screen Test")
        self._init_gl()
        self.big_screen = BigScreen(0.0, 0.0, 0.0)
        self._show_text()

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.05, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _hall_light_level(self):
        return self.dark_level if self.hall_dark else 1.0

    def _apply_hall_light(self):
        level = self._hall_light_level()
        glLightfv(GL_LIGHT0, GL_DIFFUSE, tuple(channel * level for channel in self.light_diffuse) + (1.0,))
        glLightfv(GL_LIGHT0, GL_AMBIENT, tuple(channel * level for channel in self.light_ambient) + (1.0,))
        glClearColor(*(channel * level for channel in self.background), 1.0)

    def _screen_brightness(self):
        fade_progress = (self.elapsed - self.fade_started) / self.fade_duration
        return min(max(fade_progress, 0.0), 1.0)

    def _draw_floor(self):
        glColor3f(0.12, 0.08, 0.14)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        size = 20.0
        glVertex3f(-size, 0.0, -size)
        glVertex3f(-size, 0.0, size)
        glVertex3f(size, 0.0, size)
        glVertex3f(size, 0.0, -size)
        glEnd()

    def _camera(self):
        screen_middle = self.big_screen.lift + self.big_screen.height / 2.0
        if self.front_view:
            sway = math.sin(self.elapsed * 0.3) * 1.5
            eye = (sway, screen_middle - 0.5, 11.0)
            return eye, (sway * 0.3, screen_middle, 0.0)
        orbit = self.elapsed * 0.35
        eye = (math.sin(orbit) * 14.0, screen_middle + 1.5, math.cos(orbit) * 14.0)
        return eye, (0.0, screen_middle - 1.0, 0.0)

    def _show_text(self):
        self.big_screen.display_2_languages_text(self.english_file, self.german_file, size=self.text_size)

    def _toggle_text(self):
        if self.big_screen.text_texture is None:
            self._show_text()
        else:
            self.big_screen.clear_text()

    def run(self):
        running = True
        while running:
            delta_seconds = self.clock.tick(60) / 1000.0
            self.elapsed += delta_seconds
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_1:
                        self.front_view = True
                    elif event.key == K_2:
                        self.front_view = False
                    elif event.key == K_f:
                        self.fade_started = self.elapsed
                    elif event.key == K_d:
                        self.hall_dark = not self.hall_dark
                    elif event.key == K_t:
                        self._toggle_text()
            self.big_screen.update(delta_seconds)
            self._apply_hall_light()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            eye, target = self._camera()
            gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)
            glLightfv(GL_LIGHT0, GL_POSITION, (2.0, 8.0, 6.0, 1.0))
            self._draw_floor()
            self.big_screen.draw(self._screen_brightness())
            pygame.display.flip()
        pygame.quit()


def main():
    print("Press 1 for the front view, 2 to orbit the screen, F to replay the fade-in, D to darken the hall, "
          "T to show/hide the text")
    BigScreenTest().run()


if __name__ == "__main__":
    main()
