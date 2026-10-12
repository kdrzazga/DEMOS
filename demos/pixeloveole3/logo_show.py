import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from demos.pixeloveole3.scene import LibraryScene
from lib.demo_phases import CameraInterpolationHelper
from lib.pixelove_ole.logo import PixeloveOleLogo


class LogoStage:
    """Views the 3D Pixelove Ole logo head-on with a gentle sway. The whole
    logo can be shrunk and slid across the screen (`screen_scale`,
    `screen_offset` in normalised device units) by post-projection, so the
    perspective of the logo itself never changes."""

    def __init__(self, width, height, lower_word="LOVE", field_of_view=40.0, distance=13.0,
                 target_height=0.7, pitch_degrees=6.0, sway_degrees=12.0, sway_speed=0.5):
        self.width = width
        self.height = height
        self.logo = PixeloveOleLogo(lower_word=lower_word)
        self.field_of_view = field_of_view
        self.distance = distance
        self.target_height = target_height
        self.pitch = math.radians(pitch_degrees)
        self.sway = math.radians(sway_degrees)
        self.sway_speed = sway_speed
        self.screen_scale = 1.0
        self.screen_offset = (0.0, 0.0)

    def update(self, seconds):
        self.logo.update(seconds)

    def render(self, elapsed):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_FOG)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(*self.screen_offset, 0.0)
        glScalef(self.screen_scale, self.screen_scale, 1.0)
        gluPerspective(self.field_of_view, self.width / self.height, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        yaw = self.sway * math.sin(elapsed * self.sway_speed)
        eye_x = self.distance * math.cos(self.pitch) * math.sin(yaw)
        eye_y = self.target_height + self.distance * math.sin(self.pitch)
        eye_z = self.distance * math.cos(self.pitch) * math.cos(yaw)
        gluLookAt(eye_x, eye_y, eye_z, 0.0, self.target_height, 0.0, 0.0, 1.0, 0.0)
        self.logo.draw()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class LogoShow:
    """Shared state of the pixeloveole3 phases: the logo, the BIBLIOTEKA
    library scene behind it, how much of that scene is faded in and, once a
    phase takes over its camera, the (eye, target) it is viewed from. The
    logo is an overlay with its own projection, so it stays put on screen
    whatever the library camera does."""

    def __init__(self, width, height):
        self.stage = LogoStage(width, height)
        self.library = LibraryScene(width, height)
        self.elapsed = 0.0
        self.library_elapsed = 0.0
        self.library_visibility = 0.0
        self.library_shown = False
        self.library_fade_seconds = 1.0
        self.library_view = None

    @property
    def logo(self):
        return self.stage.logo

    def show_library(self, fade_seconds):
        self.library_shown = True
        self.library_fade_seconds = fade_seconds

    def current_library_view(self):
        return self.library_view or self.library.camera.view(self.library_elapsed)

    def update(self, seconds):
        self.elapsed += seconds
        self.stage.update(seconds)
        if self.library_shown:
            self.library_elapsed += seconds
            self.library_visibility = CameraInterpolationHelper.smooth(self.library_elapsed / self.library_fade_seconds)

    def render(self):
        if self.library_shown:
            self.library.render(self.library_elapsed, self.library_view)
            self._darken(1.0 - self.library_visibility)
            glClear(GL_DEPTH_BUFFER_BIT)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.stage.render(self.elapsed)

    def render_blank(self):
        self.library.render_blank()

    def _darken(self, amount):
        if amount <= 0.0:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor4f(0.0, 0.0, 0.0, amount)
        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(0.0, 1.0)
        glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()
