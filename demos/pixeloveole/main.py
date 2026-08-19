import os
import sys
from datetime import datetime

# Allow running both from the DEMOS project root (python main.py, DEFAULT_DEMO="po")
# and directly from this file (python demos/pixeloveole/main.py). Put the project
# root on sys.path for `lib.*` imports, and this folder for `stage1`..`stage5`.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
for _path in (_ROOT, _HERE):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import arcade

from arcade.color import BLACK
from lib.common import Globals
from stage1 import Stage1
from stage2 import Stage2
from stage3 import Stage3
from stage4 import Stage4
from stage5 import Stage5


class PixeloveOle(arcade.Window):

    def __init__(self, windowed=False, triggered=False):
        # Resources are referenced as relative "res/..." paths, so run from this
        # folder no matter where the process was launched (root or this file).
        os.chdir(_HERE)
        super().__init__(Globals.WIDTH, Globals.HEIGHT, "DEMO")
        self.stage4 = None
        self.stage3 = None
        self.stage2 = None
        self.set_fullscreen(Globals.fullscreen and not windowed)
        self.timer = 0
        self.stage1 = Stage1()

    def run(self):
        arcade.run()

    def on_draw(self):
        self.clear(BLACK)

        if self.timer < 200:
            self.stage1.on_draw(self.timer)

        if self.timer//1 == 200.0:
            if not Stage2.ACTIVE:
                self.stage2 = Stage2(self.timer)
        elif 200 < self.timer < Stage3.START_TIMER:
            self.stage2.on_draw(self.timer)
        elif self.timer//1 == Stage3.START_TIMER:
            self.stage3 = Stage3()
        elif Stage3.START_TIMER < self.timer < Stage4.START_TIMER:
            self.stage3.on_draw(self.timer)
        elif self.timer//1 == Stage4.START_TIMER:
            self.stage4 = Stage4()
        elif Stage4.START_TIMER < self.timer < Stage5.START_TIMER:
            self.stage4.on_draw(self.timer)
        elif self.timer//1 == Stage5.START_TIMER:
            self.stage5 = Stage5()
        elif Stage5.START_TIMER < self.timer:
            self.stage5.on_draw(self.timer)

        dur = datetime.now() - Globals.start
        print(dur)
        self.timer += Globals.TIMER_INC


if __name__ == "__main__":
    window = PixeloveOle()
    arcade.run()
