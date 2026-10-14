from demos.jack.framings import EUROPE, NORTH_AMERICA
from demos.jack.locations import LODZ, MONTE_SERENO
from demos.jack.stage import Chapter, MapEra, Stage


class Stage1996(Stage):
    def __init__(self):
        super().__init__(21, MapEra.MODERN, year_label="1996", locations=(MONTE_SERENO,))


class Stage1998(Stage):
    def __init__(self):
        super().__init__(22, MapEra.MODERN, year_label="1998")


class Stage2004(Stage):
    def __init__(self):
        super().__init__(23, MapEra.MODERN, year_label="2004", locations=(LODZ,), framing=EUROPE)


class Stage2012(Stage):
    def __init__(self):
        super().__init__(24, MapEra.MODERN, year_label="2012", locations=(MONTE_SERENO,))


CHAPTER = Chapter(NORTH_AMERICA, (Stage1996, Stage1998, Stage2004, Stage2012))
