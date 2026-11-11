import os
import sys
import time

import pygame
from pygame.locals import DOUBLEBUF, OPENGL

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.three_mirrors.mirror_renderer import MirrorRenderer
from lib.three_mirrors.reflection_governor import ReflectionGovernor
from lib.urban.glass import GreenDistrict


class GlassTowersTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.longest_step = 0.1
        self.blur_step = 0.05
        self.blur_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.sharpen_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.caption_interval = 0.5
        self.caption = ("Glass Towers [{}] {:.0f} fps - reflections: {} (walls {}), {}  "
                        "(TAB scene, UP/DOWN reflections, +/- blur, F flood lights, SPACE camera, ESC quit)")
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Glass Towers - building scenes...")
        self.clock = pygame.time.Clock()
        self.renderer = MirrorRenderer(max_reflections=1, reflection_limit=2)
        self.governor = ReflectionGovernor(self.renderer, self.frames_per_second)
        self.scenes = [GreenDistrict().build()]
        for scene in self.scenes:
            scene.prepare()
        self.scene_index = 0
        self.scene.activate(self.window_size)
        self.since_caption = self.caption_interval
        self.running = True

    @property
    def scene(self):
        return self.scenes[self.scene_index]

    def next_scene(self):
        self.scene_index = (self.scene_index + 1) % len(self.scenes)
        self.scene.activate(self.window_size)

    def show_caption(self):
        pygame.display.set_caption(self.caption.format(
            self.scene.name, self.governor.frames_per_second, self.renderer.max_reflections,
            self.renderer.reflection_budget, self.scene.status()))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_TAB:
            self.next_scene()
        elif key == pygame.K_UP:
            self.renderer.change_reflections(1)
        elif key == pygame.K_DOWN:
            self.renderer.change_reflections(-1)
        elif key in self.blur_keys:
            self.scene.change_blur(self.blur_step)
        elif key in self.sharpen_keys:
            self.scene.change_blur(-self.blur_step)
        elif key == pygame.K_f:
            self.scene.toggle_flood_lights()
        elif key == pygame.K_SPACE:
            self.scene.camera.toggle_pause()

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
            step = min(frame_seconds, self.longest_step)
            self.handle_events()
            self.scene.update(step)
            self.scene.render(self.renderer)
            pygame.display.flip()
            self.governor.observe(frame_seconds)
            self.refresh_caption(frame_seconds)
        pygame.quit()


if __name__ == "__main__":
    GlassTowersTest().run()
