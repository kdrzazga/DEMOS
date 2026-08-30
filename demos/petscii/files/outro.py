import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
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
    glClear,
    glClearColor,
    glColor3f,
    glDeleteTextures,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.green_guy import GreenGuy
from lib.helix import PetsciiHelix
from lib.cequals import Cequals


class Outro:
    """The demo's outro: the Green Guy cycling through his expressions while the
    whole picture sways and zooms in and out (exactly as green_guy_test.py does),
    over AspirationRamos.mp3 fading up from 10% to 100% volume in 1% steps every
    100 ms.

    It carries its own animation + music but no window: :meth:`begin` /
    :meth:`update` / :meth:`draw` run it inside a caller's existing OpenGL context
    (so the main demo can play it in the same window), while :meth:`run` is a
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

    def __init__(self, fps=60):

        self.credits = ('Music: Wodnik & Ramos', 'K&A+ PETSCII logo: tom3000'
                     , 'Other PETSCII graphics: KD', 'Code: KD')

        # animation config (instance attributes, easy to nudge)
        self.char_size = 24
        self.frame_ms = 200          # each head+torso combination is held this long
        self.guy_width, self.guy_height = 13, 16
        self.camera_fit = 1.4        # camera distance as a multiple of the surface
        self.sway_degrees = 10.0
        self.sway_period = 5000.0    # ms for a full left-right-left sway
        self.zoom_step = 2.0         # units the camera moves each frame
        self.zoom_near = 0.6         # closest camera distance, fraction of the fit distance
        self.zoom_far = 1.4          # farthest camera distance, fraction of the fit distance
        self.fps = fps

        # music config: start quiet and fade up
        self.music_file = "AspirationRamos.mp3"
        self.start_volume = 0.10
        self.volume_step = 0.01
        self.volume_step_ms = 100
        self.max_volume = 1.0

        self.helix_speed = 0.03

        # runtime state (filled in begin())
        self.guy = None
        self.surface = None
        self.texture = None
        self.frame = 0
        self.sway = 0.0
        self.z = 0.0
        self.running = False
        self.helix = None

    # ---- embedded lifecycle (runs in the caller's window/context) -----------
    def begin(self):
        """Build the GL resources and start the music. Requires an active OpenGL
        context (the caller's window). Call once before update()/draw()."""
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        if self.guy is None:
            self.guy = GreenGuy(self.char_size)
            # centre the 13x16 guy in the 40x25 screen; the head paste follows origin
            self.guy.origin = ((Constants.ROWS - self.guy_height) // 2,
                               (Constants.COLUMNS - self.guy_width) // 2)
        self.guy_w, self.guy_h = self.guy.size()
        self.surface = pygame.Surface((self.guy_w, self.guy_h))
        self.texture = None
        self.frame = 0
        self.texture = self._render_frame(Outro.FRAMES[self.frame])

        self.base_distance = max(self.guy_w, self.guy_h) * self.camera_fit
        self.z = self.base_distance
        self.z_near = self.base_distance * self.zoom_near
        self.z_far = self.base_distance * self.zoom_far
        self._zoom_step = self.zoom_step

        self.start_ms = pygame.time.get_ticks()
        self._start_music()

        width, height = pygame.display.get_surface().get_size()
        eye = -Constants.CAMERA_Z
        visible_half_width = eye * math.tan(math.radians(Constants.FOV / 2)) * (width / height)
        self.helix = PetsciiHelix(-0.7 * visible_half_width, self.helix_speed, Cequals(32),
                                  z_stretch=5.0, x_flatten=0.5)

    def update(self):
        """Advance one frame: cycle the expression, sway, zoom, and fade the music."""
        now = pygame.time.get_ticks()
        step = ((now - self.start_ms) // self.frame_ms) % len(Outro.FRAMES)
        if step != self.frame:
            self.frame = step
            self.texture = self._render_frame(Outro.FRAMES[self.frame])

        self.sway = self.sway_degrees * math.sin(2 * math.pi * now / self.sway_period)
        self.z += self._zoom_step
        if self.z >= self.z_far:
            self.z, self._zoom_step = self.z_far, -self.zoom_step
        elif self.z <= self.z_near:
            self.z, self._zoom_step = self.z_near, self.zoom_step

        self._fade_in_music()
        self.helix.update()

    def draw(self):
        """Draw the guy into whatever window is current, sized to its own aspect
        and centred (the projection uses the live window aspect, so it is correct
        in the demo's window or a standalone one alike)."""
        window_width, window_height = pygame.display.get_surface().get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, window_width / window_height, 1.0, 10000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.z)
        glTranslatef(3 * self.guy_w / Constants.COLUMNS, 0.0, 0.0)
        glRotatef(self.sway, 0.0, 1.0, 0.0)

        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        half_width, half_height = self.guy_w / 2, self.guy_h / 2
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, 0)
        glTexCoord2f(1, 0); glVertex3f(half_width, half_height, 0)
        glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, 0)
        glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, 0)
        glEnd()

        self.helix.draw()

    def stop_music(self):
        pygame.mixer.music.stop()

    # ---- standalone loop (opens its own window) -----------------------------
    def run(self):
        pygame.init()
        pygame.mixer.init()

        self.guy = GreenGuy(self.char_size)
        self.guy.origin = ((Constants.ROWS - self.guy_height) // 2,
                           (Constants.COLUMNS - self.guy_width) // 2)
        width, height = self.guy.size()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Outro - Green Guy")
        glClearColor(0.0, 0.0, 0.0, 1.0)

        self.begin()
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.running = False
            self.update()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw()
            pygame.display.flip()
            clock.tick(self.fps)

        self.stop_music()
        pygame.quit()

    # ---- music --------------------------------------------------------------
    def _start_music(self):
        path = os.path.join(os.path.dirname(__file__), "resources", self.music_file)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self.start_volume)
        pygame.mixer.music.play(-1)          # loop underneath the outro
        self.current_volume = self.start_volume
        self.music_start_ms = pygame.time.get_ticks()

    def _fade_in_music(self):
        """Raise the volume one step (1%) every volume_step_ms (100 ms) until it
        reaches full volume. Derived from elapsed time so it stays on schedule."""
        if self.current_volume >= self.max_volume:
            return
        elapsed = pygame.time.get_ticks() - self.music_start_ms
        steps = elapsed // self.volume_step_ms
        target = min(self.max_volume, self.start_volume + self.volume_step * steps)
        if target != self.current_volume:
            self.current_volume = target
            pygame.mixer.music.set_volume(target)

    # ---- rendering ----------------------------------------------------------
    def _render_frame(self, name):
        """Build one head+torso combination and upload it as a fresh texture,
        deleting the previous one."""
        getattr(self.guy, name)()
        self.guy.render(self.surface)
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
