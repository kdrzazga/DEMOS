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
    screen and turns slowly on the spot about his vertical axis; after about two
    and a half turns he stops side-on (parallel to the folded left-wall screen)
    and slides up into the top-left corner, where he comes to rest.
    """

    WAIT = 0     # off-screen, not started yet
    FLY = 1      # rising from below into the bottom centre, spinning
    SPIN = 2     # turning on the spot at the bottom centre
    MOVE = 3     # stopped spinning, sliding to the top-left corner
    DONE = 4     # parked in the top-left corner

    FAR_PLANE = 300.0
    EYE_TO_SCREEN = -Constants.CAMERA_Z  # positive distance from the eye to the z=0 plane

    def __init__(self, char_size=16):
        self.image = BruceLeeKick(char_size)
        self.texture = glGenTextures(1)
        self.surface = self._render_pose()
        self._upload(self.surface)

        # tunables -- kept on the instance so the choreography is easy to nudge
        self.rest_z = 0.3                     # how far forward he floats (sets his size)
        self.spin_speed = 4.0                 # degrees per frame at 25 fps
        self.fly_in_frames = int(Constants.FPS * 1.5)
        self.width_fraction = 0.55            # of the visible half-width, at most
        self.height_fraction = 0.62           # of the visible half-height, at most
        self.floor_gap_fraction = 0.15        # clearance kept below him at rest
        # he spins ~1.25 turns then stops side-on: 450 deg is 90 deg mod 360, so
        # the flat quad ends up parallel to the folded left-wall screen
        self.stop_angle = 450.0
        self.move_frames = int(Constants.FPS * 1.5)
        self.corner_x_fraction = 0.85         # how far toward the left edge he parks
        self.corner_y_fraction = 0.85         # how far toward the top edge he parks
        self.corner_scale = 0.2               # shrink to 20% (i.e. by 80%) as he parks
        self.corner_drop_heights = 2.0        # then sit this many of his parked heights lower

        self._layout()

        self.phase = BruceLeeKickAnimation.WAIT
        self.fly_timer = 0
        self.move_timer = 0
        self.move_from_x = 0.0
        self.move_from_y = 0.0
        self.angle = 0.0
        self.scale = 1.0
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

        # where he slides to after he stops spinning: near the top-left corner,
        # then dropped a few of his parked (shrunk) heights lower. He shrinks on
        # the way in, so this stays comfortably on screen.
        parked_height = 2 * self.half_height * self.corner_scale
        self.corner_x = -self.corner_x_fraction * visible_half_width
        self.corner_y = self.corner_y_fraction * visible_half_height \
            - self.corner_drop_heights * parked_height

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

    @property
    def moving(self):
        """True from the moment he stops spinning and starts sliding to the
        corner -- the cue for Yamo to rise from the bottom and take his place."""
        return self.phase in (BruceLeeKickAnimation.MOVE, BruceLeeKickAnimation.DONE)

    @property
    def settled(self):
        """True once he has finished sliding and is parked -- the cue for Yamo to
        make the same move into the central screen."""
        return self.phase == BruceLeeKickAnimation.DONE

    def start(self):
        """Launch him up from below; ignored once he is already on his way."""
        if self.started:
            return
        self.phase = BruceLeeKickAnimation.FLY
        self.fly_timer = 0
        self.move_timer = 0
        self.x = self.rest_x
        self.y = self.start_y
        self.z = self.rest_z
        self.angle = 0.0
        self.scale = 1.0

    def update(self):
        if self.phase in (BruceLeeKickAnimation.WAIT, BruceLeeKickAnimation.DONE):
            return
        if self.phase == BruceLeeKickAnimation.FLY:
            self.angle += self.spin_speed
            self._update_fly()
        elif self.phase == BruceLeeKickAnimation.SPIN:
            self.angle += self.spin_speed
            if self.angle >= self.stop_angle:
                self.angle = self.stop_angle   # freeze side-on, parallel to the left screen
                self._begin_move()
        elif self.phase == BruceLeeKickAnimation.MOVE:
            self._update_move()

    def _update_fly(self):
        self.fly_timer += 1
        progress = min(1.0, self.fly_timer / self.fly_in_frames)
        eased = 1.0 - (1.0 - progress) ** 3    # ease-out: rushes up, then settles
        self.y = self.start_y + (self.rest_y - self.start_y) * eased
        if progress >= 1.0:
            self.y = self.rest_y
            self.phase = BruceLeeKickAnimation.SPIN

    def _begin_move(self):
        self.phase = BruceLeeKickAnimation.MOVE
        self.move_timer = 0
        self.move_from_x = self.x
        self.move_from_y = self.y

    def _update_move(self):
        self.move_timer += 1
        progress = min(1.0, self.move_timer / self.move_frames)
        eased = progress * progress * (3 - 2 * progress)   # smoothstep ease-in-out
        self.x = self.move_from_x + (self.corner_x - self.move_from_x) * eased
        self.y = self.move_from_y + (self.corner_y - self.move_from_y) * eased
        self.scale = 1.0 + (self.corner_scale - 1.0) * eased   # shrink as he parks
        if progress >= 1.0:
            self.x, self.y = self.corner_x, self.corner_y
            self.scale = self.corner_scale
            self.phase = BruceLeeKickAnimation.DONE

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
        half_width = self.half_width * self.scale
        half_height = self.half_height * self.scale
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-half_width, half_height, 0.0)
        glTexCoord2f(1, 0); glVertex3f(half_width, half_height, 0.0)
        glTexCoord2f(1, 1); glVertex3f(half_width, -half_height, 0.0)
        glTexCoord2f(0, 1); glVertex3f(-half_width, -half_height, 0.0)
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
