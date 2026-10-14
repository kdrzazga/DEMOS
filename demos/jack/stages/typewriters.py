from demos.jack.locations import NEW_YORK, TOKYO, TORONTO
from demos.jack.photos import StillPhoto
from demos.jack.stage import MapEra, Stage


class StageUSA(Stage):
    def __init__(self):
        super().__init__(5, MapEra.MODERN, year_label="1947",
                         photos=(StillPhoto("JackAndHelenTramiel.jpg"),), locations=(NEW_YORK,))


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
        super().__init__(9, MapEra.MODERN, locations=(TOKYO,))
