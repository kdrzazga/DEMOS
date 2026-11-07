import os
import sys

from OpenGL.GL import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "lib", "root_effect"))

from pulse_show import PulseShow
from sine_roots3d_connected import ConnectedSineRoots3D


class PulseBackdrop:
    def __init__(self, screen_width, screen_height):
        self.roots = ConnectedSineRoots3D()
        self.roots.aspect_ratio = screen_width / screen_height
        self.pulse_show = PulseShow(self.roots)
        self.running = False

    def start(self):
        self.pulse_show.start()
        self.running = True

    def stop(self):
        self.running = False

    def update(self, real_seconds):
        if self.running:
            self.roots.update(real_seconds)

    def clear_screen(self):
        if self.running:
            glClearColor(*self.roots.background_color, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def draw(self):
        if self.running:
            self.roots.draw()
