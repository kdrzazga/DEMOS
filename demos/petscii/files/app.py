import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, K_SPACE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_TEXTURE_2D,
    glClear,
    glClearColor,
    glEnable,
)

from demos.petscii.files.dj_space_thunder import DjSpaceThunder
from demos.petscii.files.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.tilt_screen import TiltScreen


class App:
    """PETSCII demo: two noise screens that each tilt away to opposite edges."""

    WIDTH = 1150
    HEIGHT = 700
    FPS = 25

    NOISE_SECONDS = 14
    SECOND_NOISE_SECONDS = 3
    TILT_SECONDS = 3
    SHRINK_SECONDS = 3
    PAUSE_SECONDS = 1

    # screen one appears, tilts its right edge back, then slides it to the left edge;
    # after a short pause screen two covers it and does the mirror, sliding out right.
    SCENE_NOISE = 0
    SCENE_TILT = 1
    SCENE_SHRINK = 2
    SCENE_PAUSE = 3
    SCENE_NOISE2 = 4
    SCENE_TILT2 = 5
    SCENE_SHRINK2 = 6
    SCENE_COUNT = 7

    def __init__(self):
        pygame.init()
        pygame.display.set_mode((App.WIDTH, App.HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("PETSCII")
        self.clock = pygame.time.Clock()
        self.running = True
        self.frame = 0
        self.scene_frame = 0
        self.scene = App.SCENE_NOISE

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        self.surface = pygame.Surface((App.WIDTH, App.HEIGHT))
        self.surface2 = pygame.Surface((App.WIDTH, App.HEIGHT))
        self.noise = Noise(App.WIDTH, App.HEIGHT)
        self.logo = KnaLogo(char_size=16)
        self.c64 = DjSpaceThunder(char_size=16)
        self.tiltLeft = TiltScreen(App.WIDTH, App.HEIGHT)
        self.tiltRight = TiltScreen(App.WIDTH, App.HEIGHT)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(App.FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_SPACE:
                    self.set_scene((self.scene + 1) % App.SCENE_COUNT)

    def set_scene(self, scene):
        self.scene = scene
        self.scene_frame = 0
        if scene == App.SCENE_TILT:
            self.tiltLeft.reset()
        elif scene == App.SCENE_TILT2:
            self.tiltRight.reset()

    def update(self):
        self.frame += 1
        self.scene_frame += 1
        if self.scene == App.SCENE_NOISE:
            if self.scene_frame > App.FPS * App.NOISE_SECONDS:
                self.set_scene(App.SCENE_TILT)
        elif self.scene == App.SCENE_TILT:
            self.tiltLeft.tilt(self.scene_progress(App.TILT_SECONDS))
            if self.scene_frame > App.FPS * App.TILT_SECONDS:
                self.set_scene(App.SCENE_SHRINK)
        elif self.scene == App.SCENE_SHRINK:
            self.tiltLeft.shrink(self.scene_progress(App.SHRINK_SECONDS))
            if self.scene_frame > App.FPS * App.SHRINK_SECONDS:
                self.set_scene(App.SCENE_PAUSE)
        elif self.scene == App.SCENE_PAUSE:
            if self.scene_frame > App.FPS * App.PAUSE_SECONDS:
                self.set_scene(App.SCENE_NOISE2)
        elif self.scene == App.SCENE_NOISE2:
            if self.scene_frame > App.FPS * App.SECOND_NOISE_SECONDS:
                self.set_scene(App.SCENE_TILT2)
        elif self.scene == App.SCENE_TILT2:
            self.tiltRight.tilt(self.scene_progress(App.TILT_SECONDS))
            if self.scene_frame > App.FPS * App.TILT_SECONDS:
                self.set_scene(App.SCENE_SHRINK2)
        elif self.scene == App.SCENE_SHRINK2:
            self.tiltRight.shrink(self.scene_progress(App.SHRINK_SECONDS))

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (App.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_first_screen()
        if self.scene >= App.SCENE_NOISE2:
            glClear(GL_DEPTH_BUFFER_BIT)  # let the second screen cover the first
            self.draw_second_screen()

    def draw_first_screen(self):
        self.compose_first_surface()
        if self.scene == App.SCENE_NOISE:
            self.tiltLeft.draw_flat(self.surface)
        else:
            self.tiltLeft.move_right_edge(self.surface)

    def draw_second_screen(self):
        self.compose_second_surface()
        if self.scene == App.SCENE_NOISE2:
            self.tiltRight.draw_flat(self.surface2)
        else:
            self.tiltRight.move_left_edge(self.surface2)

    def compose_first_surface(self):
        """Boiling noise with the logo revealed on top; keeps animating even when covered."""
        self.noise.render(self.surface)
        if self.frame > 10:
            self.logo.render_from_corners(self.surface, transparent_space=True)

    def compose_second_surface(self):
        """Boiling noise with the DJ Space Thunder logo revealed against the right edge."""
        self.noise.render(self.surface2)
        logo_width, _ = self.c64.size()
        origin = (App.WIDTH - logo_width, 0)
        self.c64.render_from_corners(self.surface2, transparent_space=True, origin=origin)
