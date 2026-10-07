"""Plays the iny.mp4 intro once, then CrashAnimationText on a loop.

Run from the DEMOS project root:

    python -m demos.c64.c64c.test.test_crash_animation_text
    python -m demos.c64.c64c.test.test_crash_animation_text "HELLO WORLD"

The caption defaults to COMMODORE 64, which repeats O and M, so the gap
filling shows too. SPACE replays at once, otherwise it replays a second after
it ends. ESC / window-close quits.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from demos.c64.c64c.crash_animation import CrashAnimationText
from demos.c64.c64c.test.test_crash_animation import CrashAnimationTest


class CrashAnimationTextTest(CrashAnimationTest):

	def __init__(self, text, windowed=False, triggered=False):
		self.text = text
		super().__init__(windowed=windowed, triggered=triggered)

	def _make_animation(self):
		return CrashAnimationText(self.computer, self.width / self.height, self.fov, self.text, fps=self.fps)


if __name__ == "__main__":
	CrashAnimationTextTest(sys.argv[1] if len(sys.argv) > 1 else "COMMODORE 64", windowed=True).run()
