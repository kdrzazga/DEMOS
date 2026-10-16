from demos.jack.framings import JAPAN, NORTH_AMERICA
from demos.jack.locations import NEW_YORK, TOKYO, TORONTO
from lib.photos import StillPhoto
from demos.jack.overlay import resource
from demos.jack.stage import CameraBeat, Chapter, MapEra, Stage


class StageUSA(Stage):
    def __init__(self):
        super().__init__(5, MapEra.MODERN, year_label="1947",
                         photos=(StillPhoto(resource("JackAndHelenTramiel.jpg")),), locations=(NEW_YORK,))


class Stage1953(Stage):
    def __init__(self):
        super().__init__(6, MapEra.MODERN, year_label="1953", locations=(NEW_YORK,))


class Stage1956(Stage):
    def __init__(self):
        super().__init__(7, MapEra.MODERN, year_label="1956", locations=(TORONTO,))


class Stage1962(Stage):
    def __init__(self):
        super().__init__(8, MapEra.MODERN, year_label="1962")


class StageJapan(Stage):
    def __init__(self):
        super().__init__(9, MapEra.MODERN, locations=(TOKYO,), framing=JAPAN,
                         beats=(CameraBeat(0.7, NORTH_AMERICA),))


CHAPTER = Chapter(NORTH_AMERICA, (StageUSA, Stage1953, Stage1956, Stage1962, StageJapan))
