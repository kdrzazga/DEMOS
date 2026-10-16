from demos.jack.framings import EUROPE
from demos.jack.locations import AHLEM, AUSCHWITZ, LITZMANNSTADT, LODZ
from lib.photos import LivingPhoto, StillPhoto, SwayingPhoto
from demos.jack.overlay import resource
from demos.jack.revived_photoLODZ import RevivedPhoto
from demos.jack.stage import Chapter, MapEra, Stage


class StageLodz(Stage):
    def __init__(self):
        super().__init__(1, MapEra.PRE_WAR, year_label="1928-39",
                         photos=(LivingPhoto(RevivedPhoto(), until_second=10.0),
                                 SwayingPhoto(resource("family-tree.png"), from_second=10.0)),
                         locations=(LODZ,))


class StageWW2(Stage):
    def __init__(self):
        super().__init__(2, MapEra.WAR, year_label="1939-44",
                         photos=(StillPhoto(resource("LodzPiotrkowska40s.png")),), locations=(LITZMANNSTADT,))


class StageAuschwitz(Stage):
    def __init__(self):
        super().__init__(3, MapEra.WAR, year_label="1944-45",
                         photos=(StillPhoto(resource("mengele.jpg"), appear=0.5),), locations=(AUSCHWITZ,))


class Stage1945(Stage):
    def __init__(self):
        super().__init__(4, MapEra.WAR, year_label="1945", locations=(AHLEM,))


CHAPTER = Chapter(EUROPE, (StageLodz, StageWW2, StageAuschwitz, Stage1945))
