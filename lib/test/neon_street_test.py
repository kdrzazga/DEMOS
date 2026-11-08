import os
import sys
import time

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.three_mirrors.mirror_renderer import MirrorRenderer
from lib.three_mirrors.reflection_governor import ReflectionGovernor
from lib.urban.neon import NeonStreetScene


class NeonStreetTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.longest_step = 0.1
        self.field_of_view = 55.0
        self.fog_density = 0.011
        self.blur_step = 0.05
        self.blur_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.sharpen_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.caption_interval = 0.5
        self.caption = ("Neon Street {:.0f} fps - glass reflections: {} (walls {}), blur: {:.2f}, rain: {}  "
                        "(UP/DOWN reflections, +/- blur, R rain, SPACE camera, ESC quit)")
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Neon Street - building the city...")
        self.clock = pygame.time.Clock()
        self.scene = NeonStreetScene(seed=7)
        self.init_gl()
        self.scene.build()
        self.scene.configure()
        self.renderer = MirrorRenderer(max_reflections=1, reflection_limit=1)
        self.governor = ReflectionGovernor(self.renderer, self.frames_per_second)
        self.renderer.reflection_budget = 4
        self.since_caption = self.caption_interval
        self.running = True

    def init_gl(self):
        fog = self.scene.palette.fog
        glViewport(0, 0, *self.window_size)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_LINE_SMOOTH)
        glClearColor(*fog)
        glClearStencil(0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, fog)
        glHint(GL_FOG_HINT, GL_FASTEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.2, 400.0)
        glMatrixMode(GL_MODELVIEW)

    def show_caption(self):
        pygame.display.set_caption(self.caption.format(
            self.governor.frames_per_second, self.renderer.max_reflections, self.renderer.reflection_budget,
            self.scene.blur, "on" if self.scene.rain.enabled else "off"))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_UP:
            self.renderer.change_reflections(1)
        elif key == pygame.K_DOWN:
            self.renderer.change_reflections(-1)
        elif key in self.blur_keys:
            self.scene.set_blur(self.scene.blur + self.blur_step)
        elif key in self.sharpen_keys:
            self.scene.set_blur(self.scene.blur - self.blur_step)
        elif key == pygame.K_r:
            self.scene.rain.toggle()
        elif key == pygame.K_SPACE:
            self.scene.camera.toggle_pause()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glLoadIdentity()
        self.scene.camera.look()
        self.renderer.render(self.scene.reflector_set, self.scene, self.scene.camera.eye())
        pygame.display.flip()

    def refresh_caption(self, seconds):
        self.since_caption += seconds
        if self.since_caption >= self.caption_interval:
            self.since_caption = 0.0
            self.show_caption()

    def run(self):
        previous_moment = time.perf_counter()
        while self.running:
            self.clock.tick(self.frames_per_second)
            moment = time.perf_counter()
            frame_seconds = moment - previous_moment
            previous_moment = moment
            self.handle_events()
            self.scene.update(min(frame_seconds, self.longest_step))
            self.draw()
            self.governor.observe(frame_seconds)
            self.refresh_caption(frame_seconds)
        pygame.quit()


if __name__ == "__main__":
    NeonStreetTest().run()
