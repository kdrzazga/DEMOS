"""Commodore 64 demo - pygame + OpenGL front-end.

Run from the DEMOS project root:

    python -m demos.c64.demo            # fullscreen
    python -m demos.c64.demo w          # windowed
    python main.py c64 w                # via the top-level launcher

Plays the iny.mp4 intro, then the Commodore 64 is smashed: the keys spelling
the caption fly off into the distance and come back as that caption, the rest
of the machine falls away. When the caption has been held, the demo ends.
ESC / window-close quits at any time.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from OpenGL.GL import *

from lib import Globals
from lib.pygame_demo import PygameDemo
from demos.c64.c64c.commodore64 import Commodore64
from demos.c64.c64c.crash_animation import CrashAnimationText
from demos.c64.intro import IntroVideo
from demos.c64.scene import setup_scene


class C64Demo(PygameDemo):

	def __init__(self, windowed=False, triggered=False, caption="KOMODA & AMIGA PLUS"):
		self.caption = caption
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
		self.intro_video = "iny.mp4"
		self.intro_audio = "iny.wav"
		self.caption_hold_seconds = 4.0
		super().__init__(1280, 800, "Commodore 64", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		aspect = self.width / self.height
		setup_scene(aspect, self.fov, self.background)

		self.computer = Commodore64()
		self.computer.build()
		self.animation = CrashAnimationText(self.computer, aspect, self.fov, self.caption, fps=self.fps,
		                                    caption_hold_seconds=self.caption_hold_seconds)
		self.intro = IntroVideo(os.path.join(self.resources, self.intro_video),
		                        os.path.join(self.resources, self.intro_audio), aspect)

	def step(self):
		if self.intro:
			self.intro.render()
			if self.intro.done:
				self.intro.destroy()
				self.intro = None
			return

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.animation.update()
		self.animation.draw()
		if self.animation.done:
			self._finish()

	def _finish(self):
		self.running = False
		print(Globals.get_duration())
		print("BYE !")


def c64_demo(windowed=False, triggered=False):
	C64Demo(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
	args = [arg.lower() for arg in sys.argv[1:]]
	c64_demo(windowed=any(arg in ("w", "window", "windowed") for arg in args),
	         triggered=any(arg in ("t", "trigger", "triggered") for arg in args))
