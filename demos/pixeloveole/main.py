import importlib.util
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
from lib.base_demo import BaseDemo

# `lib` resolves to the shared DEMOS/lib package (needed for lib.tunnel etc.), so
# load pixeloveole's own config from this folder's lib/common.py explicitly and
# register it as `lib.common`. main.py and every stage then use the local file.
_common_path = os.path.join(_HERE, "lib", "common.py")
_spec = importlib.util.spec_from_file_location("lib.common", _common_path)
_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_common)
sys.modules["lib.common"] = _common

from lib.common import Globals
from stage1 import Stage1
from stage2 import Stage2
from stage3 import Stage3
from stage4 import Stage4
from stage5 import Stage5


class PixeloveOle(arcade.Window, BaseDemo):

    def __init__(self, windowed=False, triggered=False):
        # Resources are referenced as relative "res/..." paths, so run from this
        # folder no matter where the process was launched (root or this file).
        os.chdir(_HERE)
        arcade.Window.__init__(self, Globals.WIDTH, Globals.HEIGHT, "DEMO")
        BaseDemo.__init__(self, windowed=windowed, triggered=triggered)
        self.stage4 = None
        self.stage3 = None
        self.stage2 = None
        self.set_fullscreen(Globals.fullscreen and not windowed)
        self.timer = 0
        self.stage1 = Stage1()
        # When triggered, hold on a blank screen with the music silenced until
        # the first mouse click (see on_start / on_mouse_press).
        if self.paused:
            self.stage1.pause_music()

    def run(self):
        arcade.run()

    def on_start(self):
        self.stage1.resume_music()

    def on_mouse_press(self, x, y, button, modifiers):
        self.trigger()

    def on_draw(self):
        self.clear(BLACK)

        if self.paused:
            return

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
