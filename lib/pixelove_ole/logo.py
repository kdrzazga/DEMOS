from lib.pixelove_ole.caption import Caption
from lib.pixelove_ole.details import Details
from lib.pixelove_ole.floor import NeonFloor
from lib.pixelove_ole.gamepad import Gamepad
from lib.pixelove_ole.invader import SpaceInvader
from lib.pixelove_ole.letters import bottom_row, bottom_row_v, top_row
from lib.pixelove_ole.skyline import Skyline
from lib.pixelove_ole.sunset import Sunset
from lib.pixelove_ole.word_morph import WordMorph


class PixeloveOleLogo:
    """3D rebuild of demos/pixeloveole/res/LOGO.png, one LogoPart per element.

    World units: 1 unit = 100 logo pixels, origin at the image centre, y up,
    the letters around z=0 and the camera expected on +z. Every part can be
    moved / rotated / hidden independently:

        floor, sunset, skyline,
        top_letters    (P I X E L O V E),
        bottom_letters (O L E), extra_v (OLE-style V),
        gamepad, invader, caption, details

    The lower row shows `lower_word` ("OLE" or "LOVE", built from O L E + V);
    `lower_row.morph_to(word)` animates between them, advanced by `update()`.
    """

    def __init__(self, lower_word="OLE"):
        self.floor = NeonFloor()
        self.sunset = Sunset()
        self.skyline = Skyline()
        self.top_letters = top_row().build_letters()
        second_row = bottom_row()
        self.bottom_letters = second_row.build_letters()
        self.extra_v = bottom_row_v(second_row)
        self.lower_row = WordMorph(second_row, [*self.bottom_letters, self.extra_v], lower_word)
        self.gamepad = Gamepad()
        self.invader = SpaceInvader()
        self.caption = Caption()
        self.details = Details()

    def parts(self):
        """All parts, roughly back to front (the order glow blending wants)."""
        return [self.details, self.sunset, self.skyline, self.floor, self.gamepad, self.invader,
                *self.top_letters, *self.bottom_letters, self.extra_v, self.caption]

    def part(self, name):
        return next(part for part in self.parts() if part.name == name)

    def update(self, delta_seconds):
        self.lower_row.update(delta_seconds)
        for part in self.parts():
            part.update(delta_seconds)

    def go_home(self):
        for part in self.parts():
            part.go_home()
        self.lower_row.snap(self.lower_row.word)

    def draw(self, exclude=()):
        for part in self.parts():
            if part not in exclude:
                part.draw()

    def release(self):
        for part in self.parts():
            part.release()
