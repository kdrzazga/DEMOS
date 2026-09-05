import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, OPENGL, QUIT
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glClear,
    glClearColor,
    glColor3f,
    glDeleteTextures,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from lib import Globals

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.green_guy import GreenGuy
from lib.helix import PetsciiHelix
from lib.cequals import Cequals
from demos.petscii.files.petscii.images.multi_petscii_image_manager import MultiPetsciiImageManager
from demos.petscii.files.typer import Typer


class Outro:
    """The demo's outro: after a short delay the Green Guy flies in from far away
    (smiling), and once he arrives the expression/sway/zoom animation runs for
    exactly 19 seconds. The AspirationRamos chiptune plays underneath the whole
    time (fading in), with outro.mp3 layered over the 19-second stretch. A rainbow
    PETSCII helix spirals on the left throughout.

    begin() / update() / draw() are frame-driven and never block, so a caller can
    run this and other animations together in one OpenGL context; run() is a
    standalone loop that opens its own window for previewing.
    """

    FRAMES = (
        "mouth_wide_open",
        "mouth_left",
        "mouth0",
        "mouth_wide_open",
        "mouth_left",
        "mouth_wide_open",
        "mouth_left",
        "mouth0",
        "mouth_o",
        "smile",
    )

    # every head+torso combination, shown in turn
    FRAMES2 = (
        "draw_guy",
        "mouth_wide_open",
        "mouth_left",
        "smile",
        "dead",
        "sad",
        "confused",
        "mouth0",
        "mouth_o",
    )

    DELAY = 0
    ARRIVE = 1
    MAIN = 2
    CREDITS = 3

    def __init__(self, fps=60):

        self.credits = ('Music: Wodnik & Ramos', 'K&A+ PETSCII logo: tom3000'
                     , 'Other PETSCII graphics: KD', 'Code: KD')
        self.talk = ('For the past 40+ years, PETSCII art has showcased the creativity of Commodore computers like '
                     'the C64. Similar to ASCII art, it uses simple characters to create expressive images, '
                     'but with a distinct retro style and limited palette. Even nowadays, it celebrates the '
                     'ingenuity of early digital artists and the legacy of vintage computing.')

        # animation config (instance attributes, easy to nudge)
        self.char_size = 24
        self.frame_ms = 200          # each head+torso combination is held this long
        self.camera_fit = 1.4        # camera distance as a multiple of the surface
        self.sway_degrees = 10.0
        self.sway_period = 5000.0    # ms for a full left-right-left sway
        self.zoom_step = 2.0         # units the camera moves each frame
        self.zoom_near = 0.6         # closest camera distance, fraction of the fit distance
        self.zoom_far = 1.4          # farthest camera distance, fraction of the fit distance
        self.fps = fps

        self.music_file = "AspirationRamos.mp3"
        self.start_volume = 0.10
        self.volume_step = 0.01
        self.volume_step_ms = 100
        self.max_volume = 1.0
        self.outro_sound_files = ("outro1.mp3", "outro2.mp3", "outro3.mp3")
        # silence after each clip before the next one starts: (after clip 1,
        # after clip 2). Tune each to fit the speech pacing of its clip.
        self.outro_gaps_ms = (333, 333)

        self.delay_ms = 2000
        self.arrive_ms = 2500
        self.main_ms = 19000
        self.guy_far_factor = 8.0

        # credits typed in the lower-left once the speech ends
        self.credits_font_size = 20
        self.credits_origin = (470, 470)  # (x, y) top-left of the credits block, screen pixels
        self.credits_line_gap = 13         # extra pixels between credit lines
        self.credits_pause_ms = 100       # pause after each caption is written

        self.helix_speed = 0.03

        # runtime state (filled in begin())
        self.guy = None
        self.surface = None
        self.texture = None
        self.current_frame_name = None
        self.sway = 0.0
        self.z = 0.0
        self.running = False
        self.helix = None
        self.phase = Outro.DELAY
        self.arrived = False
        self.main_start_ms = None
        self.guy_far_z = 0.0
        self.outro_sounds = ()
        self.outro_index = 0
        self.outro_channel = None
        self.outro_resume_ms = None
        self.speech_ended = False
        self.captions_manager = None
        self.credits_surface = None
        self.credits_typers = ()
        self.credits_texture = None
        self.credits_frame = 0
        self.credits_end_frame = 0
        self.mute_start_volume = 0.0
        self.finished = False

    # ---- embedded lifecycle (runs in the caller's window/context) -----------
    def begin(self):
        """Build the GL resources and start the music. Requires an active OpenGL
        context (the caller's window). Call once before update()/draw()."""
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        if self.guy is None:
            self.guy = GreenGuy(self.char_size)
        self.guy_w, self.guy_h = self.guy.size()
        self.fig_w, self.fig_h = self.guy.figure_size()
        self.surface = pygame.Surface((self.fig_w, self.fig_h))
        self.texture = None
        self.current_frame_name = None
        self._set_face("smile")

        self.base_distance = max(self.guy_w, self.guy_h) * self.camera_fit
        self.guy_far_z = self.base_distance * self.guy_far_factor
        self.z = self.guy_far_z
        self.z_near = self.base_distance * self.zoom_near
        self.z_far = self.base_distance * self.zoom_far
        self._zoom_step = self.zoom_step

        self.phase = Outro.DELAY
        self.arrived = False
        self.main_start_ms = None
        self.speech_ended = False
        self.start_ms = pygame.time.get_ticks()
        self._start_music()

        width, height = pygame.display.get_surface().get_size()
        eye = -Constants.CAMERA_Z
        visible_half_width = eye * math.tan(math.radians(Constants.FOV / 2)) * (width / height)
        self.helix = PetsciiHelix(-0.7 * visible_half_width, self.helix_speed, Cequals(32),
                                  z_stretch=5.0, x_flatten=0.5)
        self.captions_manager = MultiPetsciiImageManager()

    def update(self):
        now = pygame.time.get_ticks()
        self.helix.update()
        self._update_outro_music(now)
        if not self.speech_ended:
            self._fade_in_music()
        elapsed = now - self.start_ms
        if elapsed < self.delay_ms:
            self.phase = Outro.DELAY
            return
        if not self.arrived:
            self.phase = Outro.ARRIVE
            self._update_arrival(now, elapsed)
        elif not self.speech_ended:
            self.phase = Outro.MAIN
            self._update_main(now)
        else:
            self.phase = Outro.CREDITS
            self._update_credits(now)

    def _update_arrival(self, now, elapsed):
        progress = min(1.0, (elapsed - self.delay_ms) / self.arrive_ms)
        eased = 1.0 - (1.0 - progress) ** 3
        self.z = self.guy_far_z + (self.base_distance - self.guy_far_z) * eased
        self.sway = self.sway_degrees * math.sin(2 * math.pi * now / self.sway_period)
        if progress >= 1.0:
            self.arrived = True
            self.main_start_ms = now
            self.z = self.base_distance
            self._zoom_step = self.zoom_step
            self._play_outro_music()

    def _update_main(self, now):
        main_elapsed = now - self.main_start_ms
        if main_elapsed >= self.main_ms:
            if not self.speech_ended:
                self.speech_ended = True
                self._set_face("smile")
                self._begin_credits()
        elif self._outro_playing():
            step = (main_elapsed // self.frame_ms) % len(Outro.FRAMES)
            self._set_face(Outro.FRAMES[step])
        else:
            self._set_face("smile")   # between clips nothing is playing: rest on the smile
        self.sway = self.sway_degrees * math.sin(2 * math.pi * now / self.sway_period)
        self.z += self._zoom_step
        if self.z >= self.z_far:
            self.z, self._zoom_step = self.z_far, -self.zoom_step
        elif self.z <= self.z_near:
            self.z, self._zoom_step = self.z_near, self.zoom_step
        self.captions_manager.update()

    def _begin_credits(self):
        self.credits_surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT), pygame.SRCALPHA)
        font = pygame.font.Font(Constants.FONT_PATH, self.credits_font_size)
        line_height = font.get_height() + self.credits_line_gap
        x, y = self.credits_origin
        pause = round(self.credits_pause_ms * self.fps / 1000)
        typers = []
        start = 0
        for index, line in enumerate(self.credits):
            typers.append(Typer(start, line, self.credits_surface, x, y + index * line_height,
                                self.credits_font_size))
            start += len(line) + pause
        self.credits_typers = tuple(typers)
        self.credits_end_frame = start+100
        self.credits_frame = 0
        self.mute_start_volume = self.current_volume

    def _update_credits(self, now):
        self.credits_frame += 1
        self._fade_out_music()
        self.sway = self.sway_degrees * math.sin(2 * math.pi * now / self.sway_period)
        self.credits_surface.fill((0, 0, 0, 0))
        for typer in self.credits_typers:
            typer.type(self.credits_frame, beeping=True)
        if self.credits_frame >= self.credits_end_frame:
            self.finished = True

    @property
    def main_finished(self):
        return self.arrived and self.main_start_ms is not None \
            and pygame.time.get_ticks() - self.main_start_ms >= self.main_ms

    def draw(self):
        """Draw the guy into whatever window is current, sized to its own aspect
        and centred (the projection uses the live window aspect, so it is correct
        in the demo's window or a standalone one alike)."""
        if self.phase != Outro.DELAY:
            window_width, window_height = pygame.display.get_surface().get_size()
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(45, window_width / window_height, 1.0, 100000.0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0.0, 0.0, -self.z)
            glTranslatef(3 * self.guy_w / Constants.COLUMNS, 2 * self.guy_h / Constants.ROWS, 0.0)
            glRotatef(self.sway, 0.0, 1.0, 0.0)

            glColor3f(1.0, 1.0, 1.0)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            half_width, half_height = self.fig_w / 2, self.fig_h / 2
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, 0)
            glTexCoord2f(1, 0); glVertex3f(half_width, half_height, 0)
            glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, 0)
            glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, 0)
            glEnd()

        if self.arrived:
            self.captions_manager.draw()
        self.helix.draw()
        if self.credits_surface is not None:
            self._draw_credits()

    def _draw_credits(self):
        """Blit the typed credits as a flat 2D overlay (not tilted)."""
        if self.credits_texture is None:
            self.credits_texture = glGenTextures(1)
        data = pygame.image.tobytes(self.credits_surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.credits_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.credits_surface.get_width(),
                     self.credits_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, Constants.WIDTH, Constants.HEIGHT, 0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.credits_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(0, 0, 0)
        glTexCoord2f(1, 0); glVertex3f(Constants.WIDTH, 0, 0)
        glTexCoord2f(1, 1); glVertex3f(Constants.WIDTH, Constants.HEIGHT, 0)
        glTexCoord2f(0, 1); glVertex3f(0, Constants.HEIGHT, 0)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    def stop_music(self):
        pygame.mixer.music.stop()
        for sound in self.outro_sounds:
            sound.stop()

    # ---- standalone loop (opens its own window) -----------------------------
    def run(self):
        pygame.init()
        pygame.mixer.init()

        self.guy = GreenGuy(self.char_size)
        width, height = self.guy.size()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Outro - Green Guy")
        glClearColor(0.0, 0.0, 0.0, 1.0)

        self.begin()
        clock = pygame.time.Clock()
        self.running = True
        while self.running and not self.finished:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.running = False
            self.update()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw()
            pygame.display.flip()
            clock.tick(self.fps)

        self.stop_music()
        print("Elapsed time " + str(Globals.get_duration()))
        pygame.quit()

    # ---- music --------------------------------------------------------------
    def _start_music(self):
        path = os.path.join(os.path.dirname(__file__), "resources", self.music_file)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self.start_volume)
        pygame.mixer.music.play()
        self.current_volume = self.start_volume
        self.music_start_ms = pygame.time.get_ticks()

    def _fade_in_music(self):
        if self.current_volume >= self.max_volume:
            return
        elapsed = pygame.time.get_ticks() - self.music_start_ms
        steps = elapsed // self.volume_step_ms
        target = min(self.max_volume, self.start_volume + self.volume_step * steps)
        if target != self.current_volume:
            self.current_volume = target
            pygame.mixer.music.set_volume(target)

    def _fade_out_music(self):
        fade = max(0.0, 1.0 - self.credits_frame / self.credits_end_frame)
        pygame.mixer.music.set_volume(self.mute_start_volume * fade)

    def _play_outro_music(self):
        resources = os.path.join(os.path.dirname(__file__), "resources")
        self.outro_sounds = tuple(pygame.mixer.Sound(os.path.join(resources, name))
                                  for name in self.outro_sound_files)
        self.outro_index = 0
        self.outro_channel = self.outro_sounds[0].play()
        self.outro_resume_ms = None

    def _update_outro_music(self, now):
        """Advance through the outro clips: once the current one finishes, wait the
        gap that follows it, then start the next. Frame-driven, never blocks."""
        if self.outro_index >= len(self.outro_sounds) - 1:
            return   # last clip has started (or none loaded yet): nothing left to queue
        if self.outro_channel is not None and self.outro_channel.get_busy():
            return   # current clip still playing
        if self.outro_resume_ms is None:
            self.outro_resume_ms = now + self.outro_gaps_ms[self.outro_index]
        elif now >= self.outro_resume_ms:
            self.outro_index += 1
            self.outro_channel = self.outro_sounds[self.outro_index].play()
            self.outro_resume_ms = None

    def _outro_playing(self):
        """True while an outro clip is actually sounding -- False during the gaps
        and once the last clip has ended."""
        return self.outro_channel is not None and self.outro_channel.get_busy()

    # ---- rendering ----------------------------------------------------------
    def _set_face(self, name):
        """Show the named head+torso as the current face, re-rendering only when it
        changes -- each render uploads a fresh texture, so skip needless work."""
        if name != self.current_frame_name:
            self.current_frame_name = name
            self.texture = self._render_frame(name)

    def _render_frame(self, name):
        """Build one head+torso combination and upload it as a fresh texture,
        deleting the previous one."""
        getattr(self.guy, name)()
        self.guy.render_figure(self.surface)
        if self.texture is not None:
            glDeleteTextures([self.texture])
        data = pygame.image.tobytes(self.surface, "RGBA")
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.surface.get_width(),
                     self.surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        return texture


if __name__ == "__main__":
    Outro().run()
