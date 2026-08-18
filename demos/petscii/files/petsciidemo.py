import pygame
from pygame.locals import KEYDOWN, K_SPACE
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_TEXTURE_2D,
    glClear,
    glClearColor,
    glDisable,
    glEnable,
)

from demos.petscii.files.asian_animation import AsianAnimation
from demos.petscii.files.c64_base_screen import C64BaseScreen
from demos.petscii.files.petscii.asian import Asian
from lib import Globals
from lib.floor import Floor, JumpingLettersToCaption
from lib.pygame_demo import PygameDemo
from demos.petscii.files.c64_screen import C64Screen
from demos.petscii.files.petscii.dj_space_thunder import DjSpaceThunder
from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.stage_welcome import WelcomeStage
from demos.petscii.files.tilt_screen import TiltScreen
from demos.petscii.files.winding_screen import WindingScreen


class PetsciiDemo(PygameDemo):

    NOISE_SECONDS = 6
    SECOND_NOISE_SECONDS = 2.4
    TILT_SECONDS = 2.4
    SHRINK_SECONDS = 2.4
    PAUSE_SECONDS = 1
    ASIAN_SECONDS = 3
    LEAN_SECONDS = 1.5
    NOISE_HIDE_FOLD = 0.9
    TOP_SECRET_SECONDS = 15

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
    SCENE_ENCORE2 = 10
    SCENE_COUNT = 11

    def __init__(self, windowed=False, triggered=False):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "PETSCII 3D Demo",
                         fps=Constants.FPS, windowed=windowed, triggered=triggered)
        self.floor_frame = None
        self.captions_frame = None

    def setup(self):
        self.frame = 0
        self.scene_frame = 0
        self.scene = PetsciiDemo.SCENE_WELCOME
        self.captions_frame = None
        self.encore_frame = None
        self.bajtek_frame = None
        self.floor_frame = None
        self.captions = None
        self.loading = False

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
        self.c64_screen2 = WindingScreen()
        self.c64_screen2.pulse = True
        self.c64_screen2.music_started = True
        self.c64_screen3 = C64BaseScreen()
        self.c64_screen3.music_started = True
        self.c64_screen3.target_z = TiltScreen.TILT_DEPTH
        self.floor = Floor(Constants.WIDTH, Constants.HEIGHT)
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
        elif scene == PetsciiDemo.SCENE_ENCORE:
            self.c64_screen.zoom_to_front()
            self.c64_screen.fold_to_left_wall(TiltScreen.TILT_DEPTH,
                                              PetsciiDemo.LEAN_SECONDS, Constants.FPS)
        elif scene == PetsciiDemo.SCENE_ENCORE2:
            self.c64_screen2.zoom_to_front()
            self.c64_screen2.fold_to_right_wall(TiltScreen.TILT_DEPTH,
                                                PetsciiDemo.LEAN_SECONDS, Constants.FPS)

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
        elif self.scene == PetsciiDemo.SCENE_ASIAN:
            self.asian_animation.update(self.scene_frame)
            if self.asian_animation.finished:
                self.c64_screen.zoom(1.1)
            self.c64_screen.update(self.frame)
            if self.asian_animation.finished and self.c64_screen.z >= self.c64_screen.target_z:
                if self.encore_frame is None:
                    self.encore_frame = self.frame
                elif self.frame - self.encore_frame > Constants.FPS:
                    self.set_scene(PetsciiDemo.SCENE_ENCORE)
        elif self.scene == PetsciiDemo.SCENE_ENCORE:
            self.asian_animation.update(self.scene_frame)
            self.c64_screen.update(self.frame)
            self.c64_screen2.update(self.frame)
            if self.c64_screen2.arrived():
                if self.bajtek_frame is None:
                    self.bajtek_frame = self.frame
                elif self.frame - self.bajtek_frame > Constants.FPS * PetsciiDemo.TOP_SECRET_SECONDS:
                    self.set_scene(PetsciiDemo.SCENE_ENCORE2)
        elif self.scene == PetsciiDemo.SCENE_ENCORE2:
            self.asian_animation.update(self.scene_frame)
            self.c64_screen.update(self.frame)
            self.c64_screen2.update(self.frame)
            self.c64_screen3.update(self.frame)
            if self.captions is None and self.c64_screen3.header_written(self.frame):
                self.captions = self._build_load_captions(self.frame + 60)
                self.floor.initial_frame = self.frame
            if self.captions is not None:
                self.loading = self.loading_start <= self.frame < self.loading_end
                self.c64_screen3.loading = self.loading
                self.floor.update()
                for caption in self.captions:
                    caption.update(self.frame)
                for caption in self.captions[:3]:
                    caption.visible = not self.loading
            print("Elapsed time " + str(Globals.get_duration()))

        self.noiseLeft.set_intensity(self.tiltLeft.presence())
        self.noiseRight.set_intensity(self.tiltRight.presence())

    def _build_load_captions(self, start_frame):
        top, left, size = 0.85, -1.51, 0.08
        z = TiltScreen.TILT_DEPTH + 0.1
        duration, stagger = 65, 75
        floor_level = self.floor.level_y

        def caption(text, row, order):
            return JumpingLettersToCaption(
                text, start_frame + 14*order, duration * (order + 2),
                left, top - row * size, z,
                floor_level=floor_level, letter_size=size)

        captions = [
            caption('LOAD "PETSCII BRUCE LEE",8,1', 5, 0),
            caption("SEARCHING FOR PETSCII BRUCE LEE", 7, 1),
            caption("LOADING", 8, 2),
            caption("READY.", 9, 3),
            caption("RUN", 10, 4),
        ]
        loading, ready, run = captions[2], captions[3], captions[4]
        loading_settled = loading.initial_frame + loading.duration
        gap = ready.initial_frame + ready.duration - loading_settled
        ready.duration += 5 * gap
        run.duration += 5 * gap
        self.loading_start = loading_settled + int(0.82 * Constants.FPS)
        self.loading_end = ready.initial_frame + ready.duration
        return captions

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (Constants.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.scene == PetsciiDemo.SCENE_WELCOME:
            self.welcome.draw()
            return
        if not self.c64_screen.folded_past(PetsciiDemo.NOISE_HIDE_FOLD):
            self.draw_first_screen()
        if self.scene >= PetsciiDemo.SCENE_NOISE2:
            glClear(GL_DEPTH_BUFFER_BIT)  # let the second screen cover the first
            if not self.c64_screen2.folded_past(PetsciiDemo.NOISE_HIDE_FOLD):
                self.draw_second_screen()
        if self.scene >= PetsciiDemo.SCENE_SHRINK2:
            self.c64_screen.render(self.frame)
        if self.scene >= PetsciiDemo.SCENE_ENCORE:
            self.c64_screen2.render(self.frame)
        if self.scene >= PetsciiDemo.SCENE_ENCORE2:
            self.c64_screen3.render(self.frame)
        if self.captions is not None:
            self.floor.draw(self.frame)
            glDisable(GL_DEPTH_TEST)
            for caption in self.captions:
                caption.draw()
            glEnable(GL_DEPTH_TEST)
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
