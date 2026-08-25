import math

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_DEPTH_TEST,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor3f,
    glDisable,
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

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.bruce_lee_kick import BruceLeeKick


class BruceLeeKickAnimation:
    """Bruce Lee's kick pose shown as a spinning 3D PETSCII model.

    The pose (a :class:`BruceLeeKick` picture) is rendered once to a texture and
    drawn as a single textured quad, the same way :class:`AsianAnimation`
    presents the Asian face. On :meth:`start` he flies up from just below the
    screen, settles into the bottom centre, and from there turns slowly on the
    spot about his vertical axis.
    """

    WAIT = 0
    FLY = 1
    REST = 2

    FAR_PLANE = 300.0
    EYE_TO_SCREEN = -Constants.CAMERA_Z  # positive distance from the eye to the z=0 plane

    def __init__(self, char_size=16):
        self.image = BruceLeeKick(char_size)
        self.texture = glGenTextures(1)
        self.surface = self._render_pose()
        self._upload(self.surface)

        # tunables -- kept on the instance so the choreography is easy to nudge
        self.rest_z = 0.3                     # how far forward he floats (sets his size)
        self.spin_speed = 2.0                 # degrees per frame: a slow turn at 25 fps
        self.fly_in_frames = int(Constants.FPS * 1.5)
        self.width_fraction = 0.55            # of the visible half-width, at most
        self.height_fraction = 0.62           # of the visible half-height, at most
        self.floor_gap_fraction = 0.15        # clearance kept below him at rest

        self._layout()

        self.phase = BruceLeeKickAnimation.WAIT
        self.fly_timer = 0
        self.angle = 0.0
        self.x = self.rest_x
        self.y = self.start_y
        self.z = self.rest_z

    # ---- placement ------------------------------------------------------
    def _layout(self):
        """Size the quad to the figure and work out where he flies from and to."""
        image_aspect = self.surface.get_width() / self.surface.get_height()
        eye_distance = BruceLeeKickAnimation.EYE_TO_SCREEN - self.rest_z
        visible_half_height = eye_distance * math.tan(math.radians(Constants.FOV / 2))
        visible_half_width = visible_half_height * (Constants.WIDTH / Constants.HEIGHT)

        self._fit_to_screen(image_aspect, visible_half_width, visible_half_height)

        self.rest_x = 0.0
        self.rest_y = -visible_half_height + self.half_height \
            + self.floor_gap_fraction * visible_half_height
        # start fully below the bottom edge so he rises into view
        self.start_y = -(visible_half_height + 2 * self.half_height)

    def _fit_to_screen(self, image_aspect, visible_half_width, visible_half_height):
        """Fit the figure into the lower screen, binding on whichever of width or
        height runs out first so it never overflows regardless of font metrics."""
        max_half_width = self.width_fraction * visible_half_width
        max_half_height = self.height_fraction * visible_half_height
        if max_half_width / max_half_height > image_aspect:
            self.half_height = max_half_height
            self.half_width = self.half_height * image_aspect
        else:
            self.half_width = max_half_width
            self.half_height = self.half_width / image_aspect

    # ---- choreography ---------------------------------------------------
    @property
    def started(self):
        return self.phase != BruceLeeKickAnimation.WAIT

    def start(self):
        """Launch him up from below; ignored once he is already on his way."""
        if self.started:
            return
        self.phase = BruceLeeKickAnimation.FLY
        self.fly_timer = 0
        self.x = self.rest_x
        self.y = self.start_y
        self.z = self.rest_z
        self.angle = 0.0

    def update(self):
        if self.phase == BruceLeeKickAnimation.WAIT:
            return
        self.angle = (self.angle + self.spin_speed) % 360.0
        if self.phase == BruceLeeKickAnimation.FLY:
            self._update_fly()

    def _update_fly(self):
        self.fly_timer += 1
        progress = min(1.0, self.fly_timer / self.fly_in_frames)
        eased = 1.0 - (1.0 - progress) ** 3    # ease-out: rushes up, then settles
        self.y = self.start_y + (self.rest_y - self.start_y) * eased
        if progress >= 1.0:
            self.y = self.rest_y
            self.phase = BruceLeeKickAnimation.REST

    # ---- drawing --------------------------------------------------------
    def draw(self):
        if self.phase == BruceLeeKickAnimation.WAIT:
            return
        self._begin_3d()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)               # always ride on top of the screens
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.half_width, self.half_height, 0.0)
        glTexCoord2f(1, 0); glVertex3f(self.half_width, self.half_height, 0.0)
        glTexCoord2f(1, 1); glVertex3f(self.half_width, -self.half_height, 0.0)
        glTexCoord2f(0, 1); glVertex3f(-self.half_width, -self.half_height, 0.0)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, Constants.WIDTH / Constants.HEIGHT, 0.1,
                       BruceLeeKickAnimation.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    # ---- texture --------------------------------------------------------
    def _render_pose(self):
        """Render the kick to a tightly cropped, transparent surface so the quad
        is exactly the figure -- his bottom centre then lands where we place it."""
        cell_width, cell_height = self.image.font(self.image.char_size).size("W")
        full = pygame.Surface(self.image.size(), pygame.SRCALPHA)
        self.image.render(full, transparent_space=True)
        top, left, bottom, right = self._content_bounds()
        rect = pygame.Rect(left * cell_width, top * cell_height,
                           (right - left + 1) * cell_width,
                           (bottom - top + 1) * cell_height)
        return full.subsurface(rect).copy()

    def _content_bounds(self):
        """(top, left, bottom, right) cell bounds of the non-blank figure."""
        top, left = Constants.ROWS, Constants.COLUMNS
        bottom, right = 0, 0
        for row in range(Constants.ROWS):
            for column in range(Constants.COLUMNS):
                if not self.image.is_blank(row, column):
                    top, bottom = min(top, row), max(bottom, row)
                    left, right = min(left, column), max(right, column)
        return top, left, bottom, right

    def _upload(self, surface):
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(),
                     surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
