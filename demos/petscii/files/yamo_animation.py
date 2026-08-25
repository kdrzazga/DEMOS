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
from demos.petscii.files.petscii.yamo import Yamo


class YamoAnimation:
    """The Yamo PETSCII picture shown as a spinning 3D model.

    Presents Yamo exactly as :class:`BruceLeeKickAnimation` presents the Bruce
    Lee kick: rendered once to a texture and drawn as a single textured quad that
    flies up from below the screen and turns slowly on the spot. On :meth:`settle`
    it stops spinning and slides+shrinks to a given spot, turning to face front
    (parallel to the central screen), where it comes to rest.

    Yamo's grid is not the usual 40x25, so its real size is read from the picture
    data rather than from :class:`Constants` -- everything else matches.
    """

    WAIT = 0     # off-screen, not started yet
    FLY = 1      # rising from below into the bottom centre, spinning
    SPIN = 2     # turning on the spot at the bottom centre
    MOVE = 3     # stopped spinning, sliding+shrinking to its settle spot
    DONE = 4     # parked, facing front

    FAR_PLANE = 300.0
    EYE_TO_SCREEN = -Constants.CAMERA_Z  # positive distance from the eye to the z=0 plane

    def __init__(self, char_size=16):
        self.image = Yamo(char_size)
        self.rows = len(self.image.chars)
        self.columns = len(self.image.chars[0])
        self.texture = glGenTextures(1)
        self.surface = self._render_pose()
        self._upload(self.surface)

        # tunables -- kept on the instance so the choreography is easy to nudge
        self.rest_z = 0.3                     # how far forward it floats (sets its size)
        self.spin_speed = 2.0                 # degrees per frame: a slow turn at 25 fps
        self.fly_in_frames = int(Constants.FPS * 1.5)
        self.width_fraction = 0.55            # of the visible half-width, at most
        self.height_fraction = 0.62           # of the visible half-height, at most
        self.floor_gap_fraction = 0.15        # clearance kept below it at rest
        self.move_frames = int(Constants.FPS * 1.5)
        self.settle_scale = 0.2               # shrink to 20% as it settles, like Bruce
        self.min_spin_angle = 360.0           # complete a full turn before it may settle
        self.settle_pixel_drop = 30           # land this many pixels below the given target

        self._layout()

        self.phase = YamoAnimation.WAIT
        self.fly_timer = 0
        self.move_timer = 0
        self.move_from_x = 0.0
        self.move_from_y = 0.0
        self.move_from_angle = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_angle = 0.0
        self.angle = 0.0
        self.scale = 1.0
        self.x = self.rest_x
        self.y = self.start_y
        self.z = self.rest_z

    # ---- placement ------------------------------------------------------
    def _layout(self):
        """Size the quad to the figure and work out where it flies from and to."""
        image_aspect = self.surface.get_width() / self.surface.get_height()
        eye_distance = YamoAnimation.EYE_TO_SCREEN - self.rest_z
        visible_half_height = eye_distance * math.tan(math.radians(Constants.FOV / 2))
        visible_half_width = visible_half_height * (Constants.WIDTH / Constants.HEIGHT)

        self._fit_to_screen(image_aspect, visible_half_width, visible_half_height)

        self.rest_x = 0.0
        self.rest_y = -visible_half_height + self.half_height \
            + self.floor_gap_fraction * visible_half_height
        # start fully below the bottom edge so it rises into view
        self.start_y = -(visible_half_height + 2 * self.half_height)

        # the full view is Constants.HEIGHT pixels tall, so convert the pixel drop
        # applied at the end of the settle slide into world units here
        self.settle_world_drop = self.settle_pixel_drop \
            * (2 * visible_half_height) / Constants.HEIGHT

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
        return self.phase != YamoAnimation.WAIT

    def start(self):
        """Launch it up from below; ignored once it is already on its way."""
        if self.started:
            return
        self.phase = YamoAnimation.FLY
        self.fly_timer = 0
        self.move_timer = 0
        self.x = self.rest_x
        self.y = self.start_y
        self.z = self.rest_z
        self.angle = 0.0
        self.scale = 1.0

    def settle(self, target_x, target_y):
        """Stop spinning and slide+shrink to (target_x, target_y), turning to
        face front. Only takes effect once it has flown in and turned at least a
        full rotation (so callers may call it every frame); ignored once the move
        has begun."""
        if self.phase != YamoAnimation.SPIN or self.angle < self.min_spin_angle:
            return
        self.target_x = target_x
        self.target_y = target_y - self.settle_world_drop   # a touch lower than the given target
        self.target_angle = math.ceil(self.angle / 360.0) * 360.0  # forward to face front
        self.move_timer = 0
        self.move_from_x = self.x
        self.move_from_y = self.y
        self.move_from_angle = self.angle
        self.phase = YamoAnimation.MOVE

    def update(self):
        if self.phase in (YamoAnimation.WAIT, YamoAnimation.DONE):
            return
        if self.phase == YamoAnimation.FLY:
            self.angle += self.spin_speed
            self._update_fly()
        elif self.phase == YamoAnimation.SPIN:
            self.angle += self.spin_speed
        elif self.phase == YamoAnimation.MOVE:
            self._update_move()

    def _update_fly(self):
        self.fly_timer += 1
        progress = min(1.0, self.fly_timer / self.fly_in_frames)
        eased = 1.0 - (1.0 - progress) ** 3    # ease-out: rushes up, then settles
        self.y = self.start_y + (self.rest_y - self.start_y) * eased
        if progress >= 1.0:
            self.y = self.rest_y
            self.phase = YamoAnimation.SPIN

    def _update_move(self):
        self.move_timer += 1
        progress = min(1.0, self.move_timer / self.move_frames)
        eased = progress * progress * (3 - 2 * progress)   # smoothstep ease-in-out
        self.x = self.move_from_x + (self.target_x - self.move_from_x) * eased
        self.y = self.move_from_y + (self.target_y - self.move_from_y) * eased
        self.angle = self.move_from_angle + (self.target_angle - self.move_from_angle) * eased
        self.scale = 1.0 + (self.settle_scale - 1.0) * eased
        if progress >= 1.0:
            self.x, self.y, self.angle = self.target_x, self.target_y, self.target_angle
            self.scale = self.settle_scale
            self.phase = YamoAnimation.DONE

    # ---- drawing --------------------------------------------------------
    def draw(self):
        if self.phase == YamoAnimation.WAIT:
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
                       YamoAnimation.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    # ---- texture --------------------------------------------------------
    def _render_pose(self):
        """Render Yamo to a tightly cropped, transparent surface so the quad is
        exactly the figure -- its bottom centre then lands where we place it.

        The cells are drawn one by one over Yamo's own grid, rather than through
        ``PetsciiImage.render`` (which assumes the full 40x25 screen)."""
        cell_width, cell_height = self.image.font(self.image.char_size).size("W")
        cell_size = (cell_width, cell_height)
        full = pygame.Surface((self.columns * cell_width, self.rows * cell_height),
                              pygame.SRCALPHA)
        for row in range(self.rows):
            for column in range(self.columns):
                if not self.image.is_blank(row, column):
                    self.image.draw_cell(full, self.image.char_size, cell_size, row, column)
        top, left, bottom, right = self._content_bounds()
        rect = pygame.Rect(left * cell_width, top * cell_height,
                           (right - left + 1) * cell_width,
                           (bottom - top + 1) * cell_height)
        return full.subsurface(rect).copy()

    def _content_bounds(self):
        """(top, left, bottom, right) cell bounds of the non-blank figure."""
        top, left = self.rows, self.columns
        bottom, right = 0, 0
        for row in range(self.rows):
            for column in range(self.columns):
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
