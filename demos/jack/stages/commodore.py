from demos.jack.framings import NORTH_AMERICA
from demos.jack.locations import CHICAGO, VALLEY_FORGE
from demos.jack.photos import StillPhoto
from demos.jack.stage import Chapter, MapEra, Stage


class Stage1971(Stage):
    def __init__(self):
        super().__init__(10, MapEra.MODERN, year_label="1971", locations=(VALLEY_FORGE,))


class Stage1977PET(Stage):
    def __init__(self):
        super().__init__(11, MapEra.MODERN, year_label="1977")


class StageEarly80s(Stage):
    def __init__(self):
        super().__init__(12, MapEra.MODERN, year_label="Early 1980s")


class Stage1983(Stage):
    def __init__(self):
        super().__init__(13, MapEra.MODERN, year_label="1983")


class StageJan1984(Stage):
    def __init__(self):
        super().__init__(14, MapEra.MODERN, year_label="January 1984",
                         photos=(StillPhoto("CommodoreInternational  1984Windter CES.jpg"),
                                 StillPhoto("magazine.jpg")),
                         locations=(CHICAGO,))


CHAPTER = Chapter(NORTH_AMERICA, (Stage1971, Stage1977PET, StageEarly80s, Stage1983, StageJan1984))
