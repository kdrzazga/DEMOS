from demos.jack.framings import NORTH_AMERICA
from demos.jack.locations import SUNNYVALE, WASHINGTON
from demos.jack.photos import StillPhoto
from demos.jack.stage import Chapter, MapEra, Stage


class Stage1984(Stage):
    def __init__(self):
        super().__init__(15, MapEra.MODERN, year_label="1984",
                         photos=(StillPhoto("Leo.jpg"),), locations=(SUNNYVALE,))


class StageMid80s(Stage):
    def __init__(self):
        super().__init__(16, MapEra.MODERN, year_label="Mid-1980s")


class Stage1986(Stage):
    def __init__(self):
        super().__init__(17, MapEra.MODERN, year_label="1986")


class StageLate80s(Stage):
    def __init__(self):
        super().__init__(18, MapEra.MODERN, year_label="Late 1980s", locations=(SUNNYVALE,))


class Stage1993(Stage):
    def __init__(self):
        super().__init__(19, MapEra.MODERN, year_label="1993", locations=(WASHINGTON,))


class Stage1995(Stage):
    def __init__(self):
        super().__init__(20, MapEra.MODERN, year_label="1995", locations=(SUNNYVALE,))


CHAPTER = Chapter(NORTH_AMERICA, (Stage1984, StageMid80s, Stage1986, StageLate80s, Stage1993, Stage1995))
