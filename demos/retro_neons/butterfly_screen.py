from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.animals.butterfly import Butterfly3D, WingPattern
from lib.test.butterfly_test import CreditsOverlay


class ButterflyCreditsScene:

    def __init__(self, pixel_width, pixel_height):
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.background_color = (0.55, 0.72, 0.85, 1.0)
        self.field_of_view = 45.0
        self.camera_distance = 6.0
        self.view_pitch_degrees = 25.0
        self.view_yaw_degrees = 30.0
        self.spin_degrees_per_second = 20.0
        self.butterfly = Butterfly3D()
        self.butterfly.orientation_degrees = [-90.0, 0.0, 0.0]
        self.butterfly.shape.pattern = WingPattern()
        self.butterfly.rebuild()
        self.credits_overlay = CreditsOverlay((pixel_width, pixel_height))
        self.texture = None
        self.framebuffer = None
        self.depth_buffer = None

    def prepare(self):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.pixel_width, self.pixel_height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     None)
        self.depth_buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.pixel_width, self.pixel_height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        self.framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_buffer)
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("butterfly screen framebuffer incomplete")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def update(self, seconds):
        self.view_yaw_degrees += self.spin_degrees_per_second * seconds
        self.butterfly.flap_wings(seconds)
        self.credits_overlay.update(seconds)

    def render(self):
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glViewport(0, 0, self.pixel_width, self.pixel_height)
        glDisable(GL_FOG)
        glDisable(GL_STENCIL_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glClearColor(*self.background_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.pixel_width / self.pixel_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glRotatef(self.view_pitch_degrees, 1.0, 0.0, 0.0)
        glRotatef(self.view_yaw_degrees, 0.0, 1.0, 0.0)
        self.butterfly.draw()
        self.credits_overlay.draw()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glPopAttrib()


class ButterflyWallScreen:

    def __init__(self, face, across, rise, width, height):
        self.wall_offset = 0.45
        self.corners = (face.point(across, rise, self.wall_offset),
                        face.point(across + width, rise, self.wall_offset),
                        face.point(across + width, rise + height, self.wall_offset),
                        face.point(across, rise + height, self.wall_offset))
        self.facing = face.normal
        self.pixel_height = 360
        self.scene = ButterflyCreditsScene(round(self.pixel_height * width / height), self.pixel_height)
        self.glow_spread = (1.12, 1.25)
        self.glow_strength = 0.3
        self.playing = False
        self.has_frame = False

    def prepare(self):
        self.scene.prepare()

    def update(self, seconds):
        if not self.playing:
            return
        self.scene.update(seconds)
        self.scene.render()
        self.has_frame = True

    def draw(self):
        if not self.has_frame:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.scene.texture)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        self._quad(self.corners)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glColor4f(1.0, 1.0, 1.0, self.glow_strength)
        self._quad(self._glow_corners())
        glPopAttrib()

    def _glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5 + self.facing * 0.05
        half_across = (bottom_right - bottom_left) * (0.5 * self.glow_spread[0])
        half_up = (top_left - bottom_left) * (0.5 * self.glow_spread[1])
        return (center - half_across - half_up, center + half_across - half_up,
                center + half_across + half_up, center - half_across + half_up)

    @staticmethod
    def _quad(corners):
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(corners, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
            glTexCoord2f(u, v)
            glVertex3f(*corner)
        glEnd()
