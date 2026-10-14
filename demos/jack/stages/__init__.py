from demos.jack.stages.war_years import Stage1945, StageAuschwitz, StageLodz, StageWW2
from demos.jack.stages.typewriters import Stage1953, Stage1956, Stage1962, StageJapan, StageUSA
from demos.jack.stages.commodore import Stage1971, Stage1977PET, Stage1983, StageEarly80s, StageJan1984
from demos.jack.stages.atari import Stage1984, Stage1986, Stage1993, Stage1995, StageLate80s, StageMid80s
from demos.jack.stages.last_years import Stage1996, Stage1998, Stage2004, Stage2012

STAGE_ORDER = (
    StageLodz, StageWW2, StageAuschwitz, Stage1945,
    StageUSA, Stage1953, Stage1956, Stage1962, StageJapan,
    Stage1971, Stage1977PET, StageEarly80s, Stage1983, StageJan1984,
    Stage1984, StageMid80s, Stage1986, StageLate80s, Stage1993, Stage1995,
    Stage1996, Stage1998, Stage2004, Stage2012,
)


def build_stages():
    return [stage_class() for stage_class in STAGE_ORDER]
