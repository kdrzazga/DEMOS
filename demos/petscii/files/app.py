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

from demos.petscii.files.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.tilt_screen import TiltScreen


class App:
    """PETSCII demo: a 2D noise and logo screen that then tilts away into 3D."""

    WIDTH = 1150
    HEIGHT = 700
    FPS = 25
    NOISE_SECONDS = 14

    SCENE_NOISE = 0
    SCENE_TILT = 1
    SCENE_SHRINK = 2
    SCENE_COUNT = 3

    TILT_SECONDS = 3
    SHRINK_SECONDS = 3

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
        self.noise = Noise(App.WIDTH, App.HEIGHT)
        self.logo = KnaLogo(char_size=16)
        self.tilt = TiltScreen(App.WIDTH, App.HEIGHT)

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
            self.tilt.reset()

    def update(self):
        self.frame += 1
        self.scene_frame += 1
        if self.scene == App.SCENE_NOISE:
            if self.frame > App.FPS * App.NOISE_SECONDS:
                self.set_scene(App.SCENE_TILT)
        elif self.scene == App.SCENE_TILT:
            self.tilt.tilt(self.scene_progress(App.TILT_SECONDS))
            if self.scene_frame > App.FPS * App.TILT_SECONDS:
                self.set_scene(App.SCENE_SHRINK)
        elif self.scene == App.SCENE_SHRINK:
            self.tilt.shrink(self.scene_progress(App.SHRINK_SECONDS))

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (App.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.compose_surface()
        if self.scene == App.SCENE_NOISE:
            self.tilt.draw_flat(self.surface)
        else:
            self.tilt.move_right_edge(self.surface)

    def compose_surface(self):
        """The 2D content: boiling noise with the logo revealed on top of it."""
        self.noise.render(self.surface)
        if self.frame > 10:
            self.logo.render_from_corners(self.surface, transparent_space=True)
