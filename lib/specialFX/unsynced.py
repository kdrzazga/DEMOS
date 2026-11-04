from OpenGL.GL import *


class UnsyncedPicture:
    def __init__(self, shift_left=5, shift_up=5):
        self.edge_margin = 5
        self.shift_left = shift_left
        self.shift_up = shift_up
        self.transparency = 0.5
        self.texture = None
        self.texture_size = (0, 0)
        self.steady_duration = 0.2
        self.flipped_duration = 0.05
        self.jump_count = 2
        self.time = 0.0

    def restart(self):
        self.time = 0.0

    def update(self, delta_seconds):
        self.time += delta_seconds

    def current_shift_left(self):
        cycle_duration = self.steady_duration + self.flipped_duration
        if self.time >= self.jump_count * cycle_duration:
            return self.shift_left
        cycle_time = self.time % cycle_duration
        if cycle_time < self.steady_duration:
            return self.shift_left
        return -self.shift_left

    def draw(self):
        viewport_x, viewport_y, viewport_width, viewport_height = glGetIntegerv(GL_VIEWPORT)
        copy_width = viewport_width - 2 * self.edge_margin
        copy_height = viewport_height - 2 * self.edge_margin
        if copy_width <= 0 or copy_height <= 0:
            return
        copy_left = viewport_x + self.edge_margin
        copy_bottom = viewport_y + self.edge_margin

        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_TEXTURE_BIT)
        self._grab_frame(copy_left, copy_bottom, copy_width, copy_height)
        paste_left = copy_left - self.current_shift_left()
        paste_bottom = copy_bottom + self.shift_up
        self._paste_frame(viewport_x, viewport_y, viewport_width, viewport_height,
                          paste_left, paste_bottom, copy_width, copy_height)
        glPopAttrib()

    def _grab_frame(self, left, bottom, width, height):
        if self.texture is None:
            self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        if self.texture_size != (width, height):
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
            self.texture_size = (width, height)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, left, bottom, width, height)

    def _paste_frame(self, viewport_x, viewport_y, viewport_width, viewport_height,
                     paste_left, paste_bottom, width, height):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(viewport_x, viewport_x + viewport_width, viewport_y, viewport_y + viewport_height, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glColor4f(1.0, 1.0, 1.0, 1.0 - self.transparency)
        paste_right = paste_left + width
        paste_top = paste_bottom + height
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(paste_left, paste_bottom)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(paste_right, paste_bottom)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(paste_right, paste_top)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(paste_left, paste_top)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
