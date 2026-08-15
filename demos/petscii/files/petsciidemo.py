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

from demos.petscii.files.asian_animation import AsianAnimation
from demos.petscii.files.c64_base_screen import C64BaseScreen
from demos.petscii.files.petscii.asian import Asian
from lib import Globals
from lib.pygame_demo import PygameDemo
from demos.petscii.files.c64_screen import C64Screen
from demos.petscii.files.petscii.dj_space_thunder import DjSpaceThunder
from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.stage_welcome import WelcomeStage
from demos.petscii.files.tilt_screen import TiltScreen


class PetsciiDemo(PygameDemo):
    """PETSCII demo: two noise screens that each tilt away to opposite edges."""

    NOISE_SECONDS = 6
    SECOND_NOISE_SECONDS = 2.4
    TILT_SECONDS = 2.4
    SHRINK_SECONDS = 2.4
    PAUSE_SECONDS = 1
    ASIAN_SECONDS = 3
    LEAN_SECONDS = 1.5
    SLIDE_SECONDS = 1.5

    WELCOME_SECONDS = 4

    # a welcome caption opens the demo; then screen one appears, tilts its right edge
    # back and slides to the left edge; after a pause screen two covers it and mirrors.
    SCENE_WELCOME = 0
    SCENE_NOISE = 1
    SCENE_TILT = 2
    SCENE_SHRINK = 3
    SCENE_PAUSE = 4
    SCENE_NOISE2 = 5
    SCENE_TILT2 = 6
    SCENE_SHRINK2 = 7
    SCENE_ASIAN = 8
    SCENE_ENCORE = 9
    SCENE_COUNT = 10

    def __init__(self, windowed=False, triggered=False):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "PETSCII 3D Demo",
                         fps=Constants.FPS, windowed=windowed, triggered=triggered)
        self.captions_frame = None

    def setup(self):
        self.frame = 0
        self.scene_frame = 0
        self.scene = PetsciiDemo.SCENE_WELCOME
        self.captions_frame = None
        self.encore_frame = None

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        self.surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.surface2 = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.noiseLeft = Noise(Constants.WIDTH, Constants.HEIGHT)
        self.noiseRight = Noise(Constants.WIDTH, Constants.HEIGHT)
        self.logo = KnaLogo(char_size=16)
        self.c64 = DjSpaceThunder(char_size=16)
        self.asian_animation = AsianAnimation()
        self.tiltLeft = TiltScreen(Constants.WIDTH, Constants.HEIGHT)
        self.tiltRight = TiltScreen(Constants.WIDTH, Constants.HEIGHT)
        self.c64_screen = C64Screen()
        self.c64_screen2 = C64BaseScreen()
        self.c64_screen2.music_started = True
        self.welcome = WelcomeStage()

    def step(self):
        self.update()
        self.draw()

    def handle_event(self, event):
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.set_scene((self.scene + 1) % PetsciiDemo.SCENE_COUNT)

    def set_scene(self, scene):
        self.scene = scene
        self.scene_frame = 0
        if scene == PetsciiDemo.SCENE_NOISE:
            self.noiseLeft.start()
        elif scene == PetsciiDemo.SCENE_TILT:
            self.tiltLeft.reset()
        elif scene == PetsciiDemo.SCENE_PAUSE:
            self.noiseLeft.stop()
        elif scene == PetsciiDemo.SCENE_NOISE2:
            self.noiseRight.start()
        elif scene == PetsciiDemo.SCENE_TILT2:
            self.tiltRight.reset()

    def update(self):
        self.frame += 1
        self.scene_frame += 1
        if self.scene == PetsciiDemo.SCENE_WELCOME:
            self.welcome.update(self.scene_frame)
            if self.scene_frame > Constants.FPS * PetsciiDemo.WELCOME_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_NOISE)
        elif self.scene == PetsciiDemo.SCENE_NOISE:
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
            if self.scene_frame > Constants.FPS * PetsciiDemo.SHRINK_SECONDS:
                self.noiseRight.stop()
            if self.c64_screen.caption_ready and self.captions_frame is None:
                self.captions_frame = self.frame
            if self.captions_frame is not None:
                if self.frame - self.captions_frame > Constants.FPS * PetsciiDemo.ASIAN_SECONDS:
                    self.set_scene(PetsciiDemo.SCENE_ASIAN)
            print("Elapsed time " + str(Globals.get_duration()))
        elif self.scene == PetsciiDemo.SCENE_ASIAN:
            self.asian_animation.update(self.scene_frame)
            if self.asian_animation.finished:
                self.c64_screen.zoom(1.75)
            self.c64_screen.update(self.frame)
            if self.asian_animation.finished and self.c64_screen.z >= self.c64_screen.target_z:
                if self.encore_frame is None:
                    self.encore_frame = self.frame
                elif self.frame - self.encore_frame > Constants.FPS:
                    self.set_scene(PetsciiDemo.SCENE_ENCORE)
        elif self.scene == PetsciiDemo.SCENE_ENCORE:
            self.asian_animation.update(self.scene_frame)
            self.c64_screen.lean(self.scene_progress(PetsciiDemo.LEAN_SECONDS))
            slide_frame = self.scene_frame - Constants.FPS * PetsciiDemo.LEAN_SECONDS
            if slide_frame > 0:
                self.c64_screen.slide(slide_frame / (Constants.FPS * PetsciiDemo.SLIDE_SECONDS))
            self.c64_screen.update(self.frame)
            self.c64_screen2.update(self.frame)

        self.noiseLeft.set_intensity(self.tiltLeft.presence())
        self.noiseRight.set_intensity(self.tiltRight.presence())

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (Constants.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.scene == PetsciiDemo.SCENE_WELCOME:
            self.welcome.draw()
            return
        self.draw_first_screen()
        if self.scene >= PetsciiDemo.SCENE_NOISE2:
            glClear(GL_DEPTH_BUFFER_BIT)  # let the second screen cover the first
            self.draw_second_screen()
        if self.scene >= PetsciiDemo.SCENE_SHRINK2:
            self.c64_screen.render(self.frame)
        if self.scene == PetsciiDemo.SCENE_ENCORE:
            self.c64_screen2.render(self.frame)
        if self.scene >= PetsciiDemo.SCENE_ASIAN:
            self.asian_animation.draw()

    def _asian_flown(self):
        return self.scene >= PetsciiDemo.SCENE_ASIAN and self.asian_animation.finished

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
        self.noiseLeft.render(self.surface)
        if self.frame > 10 and not self._asian_flown():
            self.logo.render_from_corners(self.surface, transparent_space=True)

    def compose_second_surface(self):
        """Boiling noise with the DJ Space Thunder logo revealed against the right edge."""
        self.noiseRight.render(self.surface2)
        if not self._asian_flown():
            logo_width, _ = self.c64.size()
            origin = (Constants.WIDTH - logo_width, 0)
            self.c64.render_from_corners(self.surface2, transparent_space=True, origin=origin)
