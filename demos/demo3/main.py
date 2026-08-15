"""demo3 - pygame + OpenGL front-end.

Run from the DEMOS project root:

    python -m demos.demo3.main            # fullscreen
    python -m demos.demo3.main w          # windowed
    python main.py demo3 w                # via the top-level launcher

Owns the single window and OpenGL context, then plays two stages in it. Intro
decodes iny.mp4 straight onto a GL texture (no separate video player, no
framework switch); when it ends it is destroyed and Stage1 - a 3D burst of 64
tumbling keyb.png cards - takes over in the very same context. ESC or closing
the window quits. Pass windowed=True while developing.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from OpenGL.GL import glClearColor, glEnable, glMatrixMode, GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW
from OpenGL.GLU import gluPerspective

from lib import Globals
from lib.pygame_demo import PygameDemo
from demos.demo3.files.intro import Intro
from demos.demo3.files.stage1 import Stage1

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Demo3(PygameDemo):

    RES_PATH = os.path.join(_ROOT, "demos", "demo3", "files", "resources")
    FOV = 45.0

    def __init__(self, windowed=False, triggered=False):
        super().__init__(1280, 720, "demo3 - keyboard toss", fps=60,
                         windowed=windowed, triggered=triggered)

    def setup(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(self.FOV, self.width / self.height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        self._stages = (Intro, Stage1)
        self._index = 0
        self.stage = self._make_stage(0)

    def _make_stage(self, index):
        return self._stages[index](self.width, self.height, self.RES_PATH, self.FOV)

    def _advance(self):
        self.stage.destroy()
        self._index += 1
        if self._index < len(self._stages):
            self.stage = self._make_stage(self._index)
        else:
            self.running = False
            print(Globals.get_duration())
            print("BYE !")

    def step(self):
        self.stage.render()
        if self.stage.done:
            self._advance()


def demo3_demo(windowed=False, triggered=False):
    Demo3(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
    args = [a.lower() for a in sys.argv[1:]]
    triggered = any(a in ("t", "trigger", "triggered") for a in args)
    windowed = any(a in ("w", "window", "windowed") for a in args)
    demo3_demo(windowed=windowed, triggered=triggered)
