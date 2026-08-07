import pygame
from pygame.locals import KEYDOWN, K_SPACE
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_TEXTURE_2D,
    glClear,
    glClearColor,
    glEnable,
)

from lib import Globals
from lib.pygame_demo import PygameDemo
from demos.petscii.files.c64_screen import C64Screen
from demos.petscii.files.petscii.dj_space_thunder import DjSpaceThunder
from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.tilt_screen import TiltScreen


class PetsciiDemo(PygameDemo):
    """PETSCII demo: two noise screens that each tilt away to opposite edges."""

    NOISE_SECONDS = 6
    SECOND_NOISE_SECONDS = 2.4
    TILT_SECONDS = 2.4
    SHRINK_SECONDS = 2.4
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

    def __init__(self, windowed=False, triggered=False):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "PETSCII",
                         fps=Constants.FPS, windowed=windowed, triggered=triggered)

    def setup(self):
        self.frame = 0
        self.scene_frame = 0
        self.scene = PetsciiDemo.SCENE_NOISE

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        self.surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.surface2 = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.noise = Noise(Constants.WIDTH, Constants.HEIGHT)
        self.logo = KnaLogo(char_size=16)
        self.c64 = DjSpaceThunder(char_size=16)
        self.tiltLeft = TiltScreen(Constants.WIDTH, Constants.HEIGHT)
        self.tiltRight = TiltScreen(Constants.WIDTH, Constants.HEIGHT)
        self.c64_screen = C64Screen()

    def step(self):
        self.update()
        self.draw()

    def handle_event(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.set_scene((self.scene + 1) % PetsciiDemo.SCENE_COUNT)

    def set_scene(self, scene):
        self.scene = scene
        self.scene_frame = 0
        if scene == PetsciiDemo.SCENE_TILT:
            self.tiltLeft.reset()
        elif scene == PetsciiDemo.SCENE_TILT2:
            self.tiltRight.reset()

    def update(self):
        self.frame += 1
        self.scene_frame += 1
        if self.scene == PetsciiDemo.SCENE_NOISE:
            if self.scene_frame > Constants.FPS * PetsciiDemo.NOISE_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_TILT)
        elif self.scene == PetsciiDemo.SCENE_TILT:
            self.tiltLeft.tilt(self.scene_progress(PetsciiDemo.TILT_SECONDS))
            if self.scene_frame > Constants.FPS * PetsciiDemo.TILT_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_SHRINK)
        elif self.scene == PetsciiDemo.SCENE_SHRINK:
            self.tiltLeft.shrink(self.scene_progress(PetsciiDemo.SHRINK_SECONDS))
            if self.scene_frame > Constants.FPS * PetsciiDemo.SHRINK_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_PAUSE)
        elif self.scene == PetsciiDemo.SCENE_PAUSE:
            if self.scene_frame > Constants.FPS * PetsciiDemo.PAUSE_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_NOISE2)
        elif self.scene == PetsciiDemo.SCENE_NOISE2:
            if self.scene_frame > Constants.FPS * PetsciiDemo.SECOND_NOISE_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_TILT2)
        elif self.scene == PetsciiDemo.SCENE_TILT2:
            self.tiltRight.tilt(self.scene_progress(PetsciiDemo.TILT_SECONDS))
            if self.scene_frame > Constants.FPS * PetsciiDemo.TILT_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_SHRINK2)
        elif self.scene == PetsciiDemo.SCENE_SHRINK2:
            self.tiltRight.shrink(self.scene_progress(PetsciiDemo.SHRINK_SECONDS))
            self.c64_screen.update(self.scene_frame)
            print("Elapsed time " + str(Globals.get_duration()))

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (Constants.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_first_screen()
        if self.scene >= PetsciiDemo.SCENE_NOISE2:
            glClear(GL_DEPTH_BUFFER_BIT)  # let the second screen cover the first
            self.draw_second_screen()
        if self.scene >= PetsciiDemo.SCENE_SHRINK2:
            self.c64_screen.render(self.frame)

    def draw_first_screen(self):
        self.compose_first_surface()
        if self.scene == PetsciiDemo.SCENE_NOISE:
            self.tiltLeft.draw_flat(self.surface)
        else:
            self.tiltLeft.move_right_edge(self.surface)

    def draw_second_screen(self):
        self.compose_second_surface()
        if self.scene == PetsciiDemo.SCENE_NOISE2:
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
        origin = (Constants.WIDTH - logo_width, 0)
        self.c64.render_from_corners(self.surface2, transparent_space=True, origin=origin)
