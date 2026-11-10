import os
import sys

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.retro_neons.night_city import NightCity
from demos.retro_neons.turning_graffiti import TurningGraffiti
from lib import Globals
from lib.pygame_demo import PygameDemo
from lib.three_mirrors.mirror_renderer import MirrorRenderer, StencilLevel
from lib.three_mirrors.screen_blur import ScreenBlur, ScreenRegion
from lib.three_mirrors.reflection_governor import ReflectionGovernor


class RainSound:

    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "rain.mp3")
        self.volume = 1.0

    def play_once(self):
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(loops=0)


class RetroNeonsShow:

    def __init__(self, screen_width, screen_height, fps):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.field_of_view = 55.0
        self.near_plane = 0.3
        self.far_plane = 1200.0
        self.appear_seconds = 3.0
        self.hold_seconds = 20.0
        self.ground_blur_pixels = 8.0
        self.ground_blur = ScreenBlur()
        self.graffiti = TurningGraffiti(fps, self.field_of_view, screen_width / screen_height)
        self.city = NightCity()
        self.city.build()
        self.graffiti_placement = self.city.camera.placement_matrix()
        self.renderer = MirrorRenderer(max_reflections=1, reflection_limit=1)
        self.governor = ReflectionGovernor(self.renderer, fps)
        self.renderer.reflection_budget = 4
        self.rain_sound = RainSound()
        self.raining = False
        self.landing_reported = False
        self.time = 0.0

    @property
    def appear_start_seconds(self):
        return self.graffiti.painting_seconds / 2.0

    @property
    def end_seconds(self):
        return self.graffiti.finish_seconds + self.city.camera.path.duration + self.hold_seconds

    @property
    def finished(self):
        return self.time >= self.end_seconds

    def setup_gl(self):
        glViewport(0, 0, self.screen_width, self.screen_height)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_LINE_SMOOTH)
        glClearStencil(0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glHint(GL_FOG_HINT, GL_FASTEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.screen_height, self.near_plane, self.far_plane)
        glMatrixMode(GL_MODELVIEW)

    def update(self, seconds):
        self.time += seconds
        self.graffiti.update(self.time)
        if not self.raining and self.time >= self.graffiti.painting_seconds:
            self.raining = True
            self.city.start_rain()
            self.rain_sound.play_once()
        if self.graffiti.finished and not self.city.camera.flying:
            self.city.camera.take_off()
        self.city.update(seconds)
        if not self.landing_reported and self.city.camera.landed:
            self.landing_reported = True
            print("Camera at balcony " + str(Globals.get_duration()))

    def observe(self, frame_seconds):
        self.governor.observe(frame_seconds)

    def draw(self):
        self.graffiti.render_canvas()
        glClearColor(*self.city.sky)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        if self.time >= self.appear_start_seconds:
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self.city.camera.look()
            self._draw_blurred_ground_mirror()
            self.renderer.render(self.city.reflector_set, self.city, self.city.camera.eye())
            self._veil(1.0 - min((self.time - self.appear_start_seconds) / self.appear_seconds, 1.0))
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.city.camera.look()
        self.graffiti.draw(self.graffiti_placement)

    def _draw_blurred_ground_mirror(self):
        self.city.draw_ground_mirror()
        self.ground_blur.apply(self.ground_blur_pixels, StencilLevel(0), ScreenRegion.of_viewport())
        glClear(GL_DEPTH_BUFFER_BIT)

    def _veil(self, opacity):
        if opacity <= 0.0:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        red, green, blue, _ = self.city.sky
        glColor4f(red, green, blue, opacity)
        glBegin(GL_QUADS)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class RetroNeons(PygameDemo):

    def __init__(self, windowed=False, triggered=False):
        self.show = None
        self.longest_frame = 0.1
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        super().__init__(1280, 720, "Retro Neons", fps=60, windowed=windowed, triggered=triggered)

    def setup(self):
        screen_width, screen_height = pygame.display.get_surface().get_size()
        self.show = RetroNeonsShow(screen_width, screen_height, self.fps)
        self.show.setup_gl()

    def step(self):
        frame_seconds = self.clock.get_time() / 1000.0
        self.show.update(min(frame_seconds, self.longest_frame))
        self.show.draw()
        self.show.observe(frame_seconds)
        if self.show.finished:
            self.running = False


if __name__ == "__main__":
    RetroNeons(windowed=True).run()
