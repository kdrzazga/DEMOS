import math

from OpenGL.GL import *

from lib.graffitti.kna.komoda_amiga_graffiti import KomodaAmigaGraffiti
from lib.graffitti.swaying_surface import SwayingSurface
from lib.rotator import AngleRotator, Edge


class LettersOnlyGraffiti(KomodaAmigaGraffiti):

    def __init__(self):
        self.first_letter_seconds = 0.3
        self.ampersand_pause_seconds = 0.4
        self.amiga_pause_seconds = 1.6
        super().__init__()

    def _komoda_letters(self):
        return [[self.komoda_pieces["K"]],
                [self.left_eye.outline, self.left_eye.letter_fill],
                [self.komoda_pieces["M1"]],
                [self.right_eye.outline, self.right_eye.letter_fill],
                [self.komoda_pieces["D"]],
                [self.komoda_pieces["A1"]]]

    def _schedule(self):
        self.left_eye.position.jump(0.0, self.komoda_centers[1])
        self.right_eye.position.jump(0.0, self.komoda_centers[3])
        komoda_letters = self._komoda_letters()
        for index, pieces in enumerate(komoda_letters):
            for piece in pieces:
                piece.spray(self._paced(self.first_letter_seconds + index * self.letter_interval_seconds),
                            self._paced(self.letter_spray_seconds))
        ampersand_start = (self.first_letter_seconds + len(komoda_letters) * self.letter_interval_seconds
                           + self.ampersand_pause_seconds)
        self.ampersand.spray(self._paced(ampersand_start), self._paced(1.2))
        amiga_start = ampersand_start + self.amiga_pause_seconds
        for index, piece in enumerate(self.amiga_pieces):
            piece.spray(self._paced(amiga_start + index * self.letter_interval_seconds),
                        self._paced(self.letter_spray_seconds))
        return self._paced(amiga_start + (len(self.amiga_pieces) - 1) * self.letter_interval_seconds
                           + self.letter_spray_seconds)


class CanvasProportions:

    def __init__(self, canvas):
        self.canvas = canvas

    def get_width(self):
        return self.canvas.pixel_width

    def get_height(self):
        return self.canvas.pixel_height


class TurningGraffiti:

    def __init__(self, fps, field_of_view, screen_aspect):
        self.screen_share = 0.8
        self.camera_distance = 7.2
        self.calm_seconds = 1.5
        self.turn_degrees = 75.0
        self.turn_seconds = 3.0
        self.graffiti = LettersOnlyGraffiti()
        visible_height = 2.0 * self.camera_distance * math.tan(math.radians(field_of_view / 2.0))
        self.surface_height = self.screen_share * min(visible_height,
                                                      visible_height * screen_aspect / self.graffiti.aspect_ratio)
        self.surface = SwayingSurface(self.surface_height * self.graffiti.aspect_ratio, self.surface_height)
        self.full_yaw = self.surface.yaw_amplitude_degrees
        self.full_pitch = self.surface.pitch_amplitude_degrees
        self.full_wave = self.surface.wave_amplitude
        self.flat_shade = self.surface.ambient + self.surface.diffuse * float(self.surface.light_direction[2])
        self.rotator = AngleRotator(CanvasProportions(self.graffiti.canvas), Edge.LEFT, self.turn_degrees,
                                    self.turn_seconds, fps, self.surface.width / 2.0)
        self.seconds = 0.0

    @property
    def painting_seconds(self):
        return self.graffiti.duration_seconds

    @property
    def turn_start_seconds(self):
        return self.painting_seconds + self.calm_seconds

    @property
    def finish_seconds(self):
        return self.turn_start_seconds + self.turn_seconds

    @property
    def turning(self):
        return self.seconds >= self.turn_start_seconds

    @property
    def finished(self):
        return self.seconds >= self.finish_seconds

    def update(self, seconds):
        self.seconds = seconds
        calm_progress = min(max((seconds - self.painting_seconds) / self.calm_seconds, 0.0), 1.0)
        restlessness = 1.0 - calm_progress
        self.surface.yaw_amplitude_degrees = self.full_yaw * restlessness
        self.surface.pitch_amplitude_degrees = self.full_pitch * restlessness
        self.surface.wave_amplitude = self.full_wave * restlessness
        self.surface.update(seconds)
        self.rotator.elapsed_frames = max(0.0, seconds - self.turn_start_seconds) * self.rotator.fps

    def render_canvas(self):
        if not self.finished:
            self.graffiti.render(self.seconds)

    def draw(self, placement):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_STENCIL_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glMultMatrixf(placement)
        glTranslatef(0.0, 0.0, -self.camera_distance)
        if self.turning:
            self._draw_turning()
        else:
            self.surface.render(self.graffiti.texture)
        glPopMatrix()
        glPopAttrib()

    def _draw_turning(self):
        corners = self.rotator.current_vertices()
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.graffiti.texture)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glColor4f(self.flat_shade, self.flat_shade, self.flat_shade, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(*corners.top_left)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(*corners.top_right)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(*corners.bottom_right)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(*corners.bottom_left)
        glEnd()
