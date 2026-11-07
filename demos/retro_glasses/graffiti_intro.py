from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.graffitti.komoda_amiga_graffiti import KomodaAmigaGraffiti
from lib.graffitti.swaying_surface import SwayingSurface
from lib.typing_effect.typed_label import TypedLabel


class GraffitiIntro:

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.field_of_view = 45.0
        self.camera_distance = 7.2
        self.surface_height = 4.8
        self.caption_text = "PROUDLY PRESENTS"
        self.caption_height = 0.24
        self.caption_gap = 0.3
        self.letters_per_second = 14.0
        self.hold_after_caption_seconds = 2.0
        self.graffiti = KomodaAmigaGraffiti()
        self.surface = SwayingSurface(self.surface_height * self.graffiti.aspect_ratio, self.surface_height)
        self.caption = TypedLabel(self.caption_text, self.caption_height, frames_per_letter=1)
        self.caption.build()
        self.active = False
        self.seconds = 0.0

    @property
    def typing_start_seconds(self):
        return self.graffiti.duration_seconds

    @property
    def typing_seconds(self):
        return len(self.caption_text) / self.letters_per_second

    @property
    def duration_seconds(self):
        return self.typing_start_seconds + self.typing_seconds + self.hold_after_caption_seconds

    def update(self, seconds):
        self.seconds = seconds
        typed_letters = int((seconds - self.typing_start_seconds) * self.letters_per_second)
        typed_letters = min(max(typed_letters, 0), len(self.caption_text))
        if typed_letters > 0 and typed_letters != self.caption.frame:
            self.caption.frame = typed_letters - 1
            self.caption.update()

    def draw(self):
        self.graffiti.render(self.seconds)
        self.surface.update(self.seconds)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glViewport(0, 0, self.screen_width, self.screen_height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.screen_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        self.surface.render(self.graffiti.texture)
        caption_center = (0.0, -self.surface_height / 2 - self.caption_gap, 0.0)
        self.caption.draw(caption_center, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        glPopAttrib()
