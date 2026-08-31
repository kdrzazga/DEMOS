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
from demos.petscii.files.asterisk_animation import AsteriskAnimation
from demos.petscii.files.bruce_lee_kick_animation import BruceLeeKickAnimation
from demos.petscii.files.bruce_walk import BruceWalk
from demos.petscii.files.yamo_animation import YamoAnimation
from demos.petscii.files.c64_base_screen import C64BaseScreen
from demos.petscii.files.petscii.asian import Asian
from lib import Globals
from lib.floor import Floor, JumpingLettersToCaption
from lib.pygame_demo import PygameDemo
from demos.petscii.files.c64_screen import C64Screen
from demos.petscii.files.petscii.dj_space_thunder import DjSpaceThunder
from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.bruce_lee import BruceLee
from demos.petscii.files.petscii.bruce_lee_stage1 import BruceLeeStage1, BruceLeeStage2
from demos.petscii.files.petscii.bruce_sprite import BruceSprite
from demos.petscii.files.petscii.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise
from demos.petscii.files.outro import Outro
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

    # once RUN has landed, the Bruce Lee stages grow up over the visible screens:
    # bruce_stage3 on the central screen a second later, bruce_stage1 on the left
    # wall a second after that
    BRUCE_STAGE_CHAR_SIZE = Constants.HEIGHT // Constants.ROWS
    BRUCE_CENTER_DELAY = 1  # seconds after RUN lands
    BRUCE_LEFT_DELAY = 2    # seconds after RUN lands
    BRUCE_FALL_DELAY = 1    # seconds after the right-panel stage finishes drawing

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

    # closing sequence, once Bruce has transferred onto the central screen: a
    # stubbed "Bruce reaches Yamo and kicks him", then the three screens zoom out
    # fast while the floor drops away, and finally the asterisk animation
    FINALE_OFF = 0
    FINALE_KICK_STUB = 1
    FINALE_CLEAR = 2
    FINALE_ASTERISKS = 3
    FINALE_OUTRO = 4

    KICK_STUB_SECONDS = 4          # hold before the zoom-out: the (not-yet-built) reach + kick on Yamo
    SCREEN_RECEDE_SPEED = 3.0      # world units/frame the screens zoom away (fast)
    SCREEN_GONE_Z = -60.0          # a screen this far back counts as gone
    FLOOR_DROP_START_SPEED = 0.1   # initial floor fall speed, world units/frame
    FLOOR_DROP_GRAVITY = 0.03      # floor fall acceleration, world units/frame^2
    FLOOR_GONE_Y = -8.0            # the floor this far down counts as gone

    def __init__(self, windowed=False, triggered=False):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "P 3D SCII  (PETSCII 3D Demo)",
                         fps=Constants.FPS, windowed=windowed, triggered=triggered)
        self.bajtek_frame = None
        self.floor_frame = None
        self.captions_frame = None

    def setup(self):
        pygame.mouse.set_visible(False)
        self.frame = 0
        self.scene_frame = 0
        self.scene = PetsciiDemo.SCENE_WELCOME
        self.captions_frame = None
        self.encore_frame = None
        self.bajtek_frame = None
        self.floor_frame = None
        self.captions = None
        self.loading = False
        self.asian_speech_frame = None
        self.asian_speaking = False
        self.asian_flew_back = False
        self.run_landed_frame = None
        self.bruce_center_revealed = False
        self.bruce_left_revealed = False
        self.bruce_right_revealed = False
        self.bruce_right_drawn_frame = None
        self.bruce_falling_started = False

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

        # three stages for now, all BruceLeeStage1; bruce_stage2 and bruce_stage3
        # will later become BruceLeeStage2 / BruceLeeStage3
        self.bruce_stage1 = BruceLeeStage1(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE)
        self.bruce_stage2 = BruceLeeStage2(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE)
        self.bruce_stage3 = BruceLeeStage1(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE)

        # a jump-pose Bruce sprite that falls into the central screen once the
        # right-panel stage has finished drawing; same char size as the stages
        self.bruce_sprite = BruceSprite(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE)

        # The three screens still fill gradually with the Bruce Lee game
        # background (bruce_stage1/2/3), exactly as before. Only the falling 2D
        # Bruce sprite is replaced: once the backgrounds have finished revealing,
        # a spinning 3D Bruce Lee kick model flies up into the bottom centre,
        # spins ~2.5 turns, stops side-on and slides to the top-left corner. As
        # he sets off, a spinning Yamo model rises from the bottom in his place.
        self.falling_bruce_enabled = False
        self.bruce_kick = BruceLeeKickAnimation()
        self.yamo = YamoAnimation()

        # once the 3D kick parks, Bruce comes alive on the left screen: he stands,
        # then walks across it (kicking through the middle), and on reaching the
        # right border transfers to the left side of the central screen
        self.bruce_walk = BruceWalk(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE, row=-1)
        self.bruce_lee_center = BruceLee(PetsciiDemo.BRUCE_STAGE_CHAR_SIZE)
        self.bruce_lee_center.origin = (-1, 0)   # (row, column) left side of the central stage
        self.bruce_lee_center.stand()
        self.bruce_shown = False
        self.bruce_transferred = False

        # closing sequence state (see the FINALE_* constants)
        self.finale_phase = PetsciiDemo.FINALE_OFF
        self.finale_timer = 0
        self.floor_drop_speed = 0.0
        self.asterisks = AsteriskAnimation()
        self.asterisks_played = False
        # the outro plays in this same window once the asterisks finish
        self.outro = Outro()

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
            self.update_welcome()
        elif self.scene == PetsciiDemo.SCENE_NOISE:
            self.update_noise()
        elif self.scene == PetsciiDemo.SCENE_TILT:
            self.update_tilt()
        elif self.scene == PetsciiDemo.SCENE_SHRINK:
            self.update_shrink()
        elif self.scene == PetsciiDemo.SCENE_PAUSE:
            self.update_pause()
        elif self.scene == PetsciiDemo.SCENE_NOISE2:
            if self.scene_frame > Constants.FPS * PetsciiDemo.SECOND_NOISE_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_TILT2)
        elif self.scene == PetsciiDemo.SCENE_TILT2:
            self.tiltRight.tilt(self.scene_progress(PetsciiDemo.TILT_SECONDS))
            if self.scene_frame > Constants.FPS * PetsciiDemo.TILT_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_SHRINK2)
        elif self.scene == PetsciiDemo.SCENE_SHRINK2:
            self.update_shrink2()
        elif self.scene == PetsciiDemo.SCENE_ASIAN:
            self.update_asian()
        elif self.scene == PetsciiDemo.SCENE_ENCORE:
            self.update_encore()
        elif self.scene == PetsciiDemo.SCENE_ENCORE2:
            self.update_encore2()
            print("Elapsed time " + str(Globals.get_duration()))

        self.noiseLeft.set_intensity(self.tiltLeft.presence())
        self.noiseRight.set_intensity(self.tiltRight.presence())

    def update_shrink2(self):
        self.tiltRight.shrink(self.scene_progress(PetsciiDemo.SHRINK_SECONDS))
        self.c64_screen.update(self.scene_frame)
        if self.scene_frame > Constants.FPS * PetsciiDemo.SHRINK_SECONDS:
            self.noiseRight.stop()
        if self.c64_screen.caption_ready and self.captions_frame is None:
            self.captions_frame = self.frame
        if self.captions_frame is not None:
            if self.frame - self.captions_frame > Constants.FPS * PetsciiDemo.ASIAN_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_ASIAN)

    def update_encore2(self):
        self.asian_animation.update(self.scene_frame)
        self.c64_screen.update(self.frame)
        self.c64_screen2.update(self.frame)
        self.c64_screen3.update(self.frame)
        if self.captions is None and self.c64_screen3.header_written(self.frame):
            self.captions = self._build_load_captions(self.frame + 60)
            self.floor.initial_frame = self.frame
        if self.captions is not None:
            self.loading = self.loading_start <= self.frame < self.loading_end
            if self.loading and self.asian_speech_frame is None:
                self.asian_speech_frame = self.frame

            # Position ownership: the manual tweaks place him during loading;
            # while speaking the glide owns x/y/z; after fly_away() the fly does.
            if not self.asian_speaking and not self.asian_flew_back \
                    and self.asian_animation.x > 0:
                self.asian_animation.x -= 0.015

            if self.loading:
                self.update_asian2()

            self.advance_asian_speech()

            self.c64_screen3.loading = self.loading
            self.floor.update()
            for caption in self.captions:
                caption.update(self.frame)
            for caption in self.captions[:3]:
                caption.visible = not self.loading
            self.hide_captions_under_bruce()

        self.reveal_bruce_stages()
        self.update_bruce_kick()
        self.update_finale()

    def update_finale(self):
        """After Bruce reaches the central screen: hold for the (stubbed) kick on
        Yamo, then zoom the three screens out fast while the floor drops away, and
        once they are gone play the closing asterisk animation."""
        if self.finale_phase == PetsciiDemo.FINALE_KICK_STUB:
            # STUB: Bruce walks up to Yamo and kicks him -- not built yet, just hold.
            self.finale_timer += 1
            if self.finale_timer >= PetsciiDemo.KICK_STUB_SECONDS * Constants.FPS:
                self.start_clear()
        elif self.finale_phase == PetsciiDemo.FINALE_CLEAR:
            self.update_clear()
        elif self.finale_phase == PetsciiDemo.FINALE_ASTERISKS:
            if not self.asterisks_played:
                self.asterisks_played = True
                self.asterisks.animate()               # blocking: plays the whole thing
                if self.asterisks.running:
                    # the main show is over; hand off to the outro in this same
                    # window (its own music replaces the show's)
                    pygame.mixer.stop()
                    self.outro.begin()
                    self.finale_phase = PetsciiDemo.FINALE_OUTRO
                else:
                    self.running = False               # ESC'd out of the asterisks -> quit
        elif self.finale_phase == PetsciiDemo.FINALE_OUTRO:
            self.outro.update()
            if self.outro.finished:
                self.running = False

    def start_clear(self):
        """Begin zooming the three screens out and dropping the floor away."""
        for screen in (self.c64_screen, self.c64_screen2, self.c64_screen3):
            screen.recede(PetsciiDemo.SCREEN_RECEDE_SPEED)
        self.floor_drop_speed = PetsciiDemo.FLOOR_DROP_START_SPEED
        self.finale_phase = PetsciiDemo.FINALE_CLEAR

    def update_clear(self):
        """The screens recede via their own update(); here the floor accelerates
        downward. Once both the screens and the floor are off-screen, hand over to
        the closing asterisk animation."""
        self.floor_drop_speed += PetsciiDemo.FLOOR_DROP_GRAVITY
        self.floor.level_y -= self.floor_drop_speed
        screens_gone = all(screen.z < PetsciiDemo.SCREEN_GONE_Z
                           for screen in (self.c64_screen, self.c64_screen2, self.c64_screen3))
        if screens_gone and self.floor.level_y < PetsciiDemo.FLOOR_GONE_Y:
            self.finale_phase = PetsciiDemo.FINALE_ASTERISKS

    def update_bruce_kick(self):
        """Choreograph the two 3D models through the finale: once the screens have
        filled with the Bruce Lee background the kick model flies up into the
        bottom centre and turns; after ~2.5 turns it stops side-on and slides to
        the top-left corner, and as it sets off Yamo rises from the bottom in its
        place, spinning."""
        if self.bruce_backgrounds_ready():
            self.bruce_kick.start()
        self.bruce_kick.update()
        if self.bruce_kick.settled:
            self.update_bruce_walk()
        if self.bruce_kick.moving:
            self.yamo.start()
        if self.bruce_kick.settled:
            # same height as Bruce, but centred in the central screen
            self.yamo.settle(0.0, self.bruce_kick.corner_y)
        self.yamo.update()

    def bruce_backgrounds_ready(self):
        """True once the last of the three screens (the right wall) has finished
        filling with the Bruce Lee game background."""
        return self.bruce_right_revealed and self.bruce_stage3.reveal_complete()

    def update_bruce_walk(self):
        """Once the 3D kick has parked, show Bruce on the left screen and walk him
        across it; when he reaches the right border, transfer him to the left side
        of the central screen (remove from the left screen, add to the central)."""
        if not self.bruce_shown:
            self.c64_screen.show_bruce_pose(self.bruce_walk.sprite)
            self.bruce_shown = True
        if self.bruce_transferred:
            return
        self.bruce_walk.update()
        if self.bruce_walk.at_border:
            self.c64_screen.show_bruce_pose(None)                     # remove from the left screen
            self.c64_screen3.show_bruce_pose(self.bruce_lee_center)   # add to the central screen
            self.bruce_transferred = True
            self.finale_phase = PetsciiDemo.FINALE_KICK_STUB          # kick off the closing sequence
            self.finale_timer = 0

    def hide_captions_under_bruce(self):
        """As bruce_stage3 grows up the central screen, hide each caption once the
        reveal line has risen to just below it."""
        front_y = self.c64_screen3.bruce_reveal_top_y()
        if front_y is None:
            return
        for caption in self.captions:
            if front_y >= caption.target_y - caption.letter_size:
                caption.visible = False

    def reveal_bruce_stages(self):
        """After RUN lands, grow bruce_stage3 up over the central screen, then a
        second later bruce_stage1 over the left-wall screen; once the left wall is
        fully drawn, grow bruce_stage2 up over the right-wall screen."""
        if self.run_landed_frame is None:
            return
        surface_size = (Constants.WIDTH, Constants.HEIGHT)
        center_frame = self.run_landed_frame + PetsciiDemo.BRUCE_CENTER_DELAY * Constants.FPS
        left_frame = self.run_landed_frame + PetsciiDemo.BRUCE_LEFT_DELAY * Constants.FPS
        if not self.bruce_center_revealed and self.frame >= center_frame:
            self.c64_screen3.reveal_bruce_stage(self.bruce_stage2, surface_size)
            self.bruce_center_revealed = True
        if not self.bruce_left_revealed and self.frame >= left_frame:
            self.c64_screen.reveal_bruce_stage(self.bruce_stage1, surface_size)
            self.bruce_left_revealed = True
        if not self.bruce_right_revealed and self.bruce_left_revealed \
                and self.bruce_stage1.reveal_complete():
            self.c64_screen2.reveal_bruce_stage(self.bruce_stage3, surface_size)
            self.bruce_right_revealed = True
        if self.falling_bruce_enabled:
            self.drop_falling_bruce()

    def drop_falling_bruce(self):
        """Once the right-panel stage has finished drawing, wait BRUCE_FALL_DELAY
        seconds, then let the jump-pose Bruce sprite fall into the central screen
        (one screen to the left of the right panel)."""
        if self.bruce_falling_started:
            return
        if self.bruce_right_revealed and self.bruce_stage2.reveal_complete() \
                and self.bruce_right_drawn_frame is None:
            self.bruce_right_drawn_frame = self.frame
        if self.bruce_right_drawn_frame is not None \
                and self.frame >= self.bruce_right_drawn_frame \
                + PetsciiDemo.BRUCE_FALL_DELAY * Constants.FPS:
            self.c64_screen3.start_falling_bruce(self.bruce_sprite)
            self.bruce_falling_started = True

    def update_asian(self):
        self.asian_animation.update(self.scene_frame)
        if self.asian_animation.finished:
            self.c64_screen.zoom(1.1)
        self.c64_screen.update(self.frame)
        if self.asian_animation.finished and self.c64_screen.z >= self.c64_screen.target_z:
            if self.encore_frame is None:
                self.encore_frame = self.frame
            elif self.frame - self.encore_frame > Constants.FPS:
                self.set_scene(PetsciiDemo.SCENE_ENCORE)

    def update_asian2(self):
        if self.asian_speaking or self.asian_flew_back:
            return
        if self.asian_animation.z < -1.51:
            self.asian_animation.z += 0.13
            self.asian_animation.y -= 0.0271
        elif self.asian_animation.y > 1:
            self.asian_animation.y -= 0.32
            self.asian_animation.z += 0.06
        if self.asian_speech_frame is not None \
                and self.frame - self.asian_speech_frame == 200:
            self.asian_animation.speak("say_meet_bruce_lee")
            self.asian_speaking = True

    def advance_asian_speech(self):
        """Run the lips while he speaks, easing him forward to the first-talk
        pose, then jump him back to the top-right corner from there exactly as
        he exits after the first talk."""
        if not self.asian_speaking:
            return
        self.asian_animation.glide_to_speak_pose()
        if not self.asian_animation.advance_speech():
            self.asian_speaking = False
            self.asian_flew_back = True
            self.asian_animation.fly_away()

    def update_encore(self):
        self.asian_animation.update(self.scene_frame)
        self.c64_screen.update(self.frame)
        self.c64_screen2.update(self.frame)
        if self.c64_screen2.arrived():
            if self.bajtek_frame is None:
                self.bajtek_frame = self.frame
            elif self.frame - self.bajtek_frame > Constants.FPS * PetsciiDemo.TOP_SECRET_SECONDS:
                self.set_scene(PetsciiDemo.SCENE_ENCORE2)

    def update_pause(self):
        if self.scene_frame > Constants.FPS * PetsciiDemo.PAUSE_SECONDS:
            self.set_scene(PetsciiDemo.SCENE_NOISE2)

    def update_shrink(self):
        self.tiltLeft.shrink(self.scene_progress(PetsciiDemo.SHRINK_SECONDS))
        if self.scene_frame > Constants.FPS * PetsciiDemo.SHRINK_SECONDS:
            self.set_scene(PetsciiDemo.SCENE_PAUSE)

    def update_tilt(self):
        self.tiltLeft.tilt(self.scene_progress(PetsciiDemo.TILT_SECONDS))
        if self.scene_frame > Constants.FPS * PetsciiDemo.TILT_SECONDS:
            self.set_scene(PetsciiDemo.SCENE_SHRINK)

    def update_noise(self):
        if self.scene_frame > Constants.FPS * PetsciiDemo.NOISE_SECONDS:
            self.set_scene(PetsciiDemo.SCENE_TILT)

    def update_welcome(self):
        self.welcome.update(self.scene_frame)
        if self.scene_frame > Constants.FPS * PetsciiDemo.WELCOME_SECONDS:
            self.set_scene(PetsciiDemo.SCENE_NOISE)

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
        # RUN lands when its letters stop jumping and settle into place
        self.run_landed_frame = run.initial_frame + run.duration
        return captions

    def scene_progress(self, seconds):
        """How far the current scene has run, as a 0..1 fraction of seconds."""
        return self.scene_frame / (Constants.FPS * seconds)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.scene == PetsciiDemo.SCENE_WELCOME:
            self.welcome.draw()
            return
        if self.finale_phase == PetsciiDemo.FINALE_ASTERISKS:
            return   # the asterisk animation, driven from update(), owns the screen now
        if self.finale_phase == PetsciiDemo.FINALE_OUTRO:
            self.outro.draw()
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
        if self.scene >= PetsciiDemo.SCENE_ENCORE2:
            if not self.bruce_kick.settled:      # once parked, the left screen shows him instead
                self.bruce_kick.draw()
            self.yamo.draw()

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
