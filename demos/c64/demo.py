"""Commodore 64 demo - pygame + OpenGL front-end.

Run from the DEMOS project root:

    python -m demos.c64.demo            # fullscreen
    python -m demos.c64.demo w          # windowed
    python main.py c64 w                # via the top-level launcher

Plays the iny.mp4 intro, then the Commodore 64 is smashed: the keys spelling
the caption fly off into the distance and come back as that caption, the rest
of the machine falls away. "PROUDLY PRESENTS" is typed under the caption,
held for a moment, and the camera flies forward through the caption. Behind
it the cassette / Datasette sequence plays (CassetteIntoDatasette), ending in
the plug's black slot - and the demo ends.
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
from demos.c64.datasette.cassette import Cassette
from demos.c64.datasette.cassette_into_datasette import CassetteIntoDatasette, ease_in_out
from demos.c64.datasette.datasette import Datasette
from demos.c64.intro import IntroVideo
from demos.c64.scene import setup_scene
from demos.c64.typed_label import TypedLabel


class C64Demo(PygameDemo):

	def __init__(self, windowed=False, triggered=False, caption="KOMODA & AMIGA PLUS", presents="PROUDLY PRESENTS"):
		self.caption = caption
		self.presents = presents
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
		self.intro_video = "iny.mp4"
		self.intro_audio = "iny.wav"
		self.presents_height = 1.4
		self.presents_gap = 1.0
		self.presents_hold_seconds = 1.0
		self.fly_through_seconds = 2.2
		self.fly_through_overshoot = 4.0
		super().__init__(1280, 800, "Commodore 64", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		aspect = self.width / self.height
		setup_scene(aspect, self.fov, self.background)

		self.computer = Commodore64()
		self.computer.build()
		self.animation = CrashAnimationText(self.computer, aspect, self.fov, self.caption, fps=self.fps,
		                                    caption_hold_seconds=0.0)
		self.presents_label = TypedLabel(self.presents, self.presents_height)
		self.presents_label.build()

		self.datasette = Datasette()
		self.datasette.build()
		self.cassette = Cassette()
		self.cassette.build()
		self.cassette_animation = CassetteIntoDatasette(self.datasette, self.cassette, aspect, self.fov)

		self.intro = IntroVideo(os.path.join(self.resources, self.intro_video),
		                        os.path.join(self.resources, self.intro_audio), aspect)
		self.phase = "intro"
		self.phase_seconds = 0.0

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	def step(self):
		if self.phase == "intro":
			self.intro.render()
			if self.intro.done:
				self.intro.destroy()
				self.intro = None
				self._enter("caption")
			return

		seconds = 1.0 / self.fps
		self.phase_seconds += seconds
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		if self.phase == "cassette":
			self._cassette_step(seconds)
		else:
			self._caption_step()

	def _caption_step(self):
		"""The smash and the caption, "PROUDLY PRESENTS", the hold and the fly-through."""
		self.animation.update()
		if self.phase == "caption" and self.animation.done:
			self._enter("presents")
		elif self.phase == "presents":
			self.presents_label.update()
			if self.presents_label.finished:
				self._enter("presents_hold")
		elif self.phase == "presents_hold" and self.phase_seconds >= self.presents_hold_seconds:
			self._enter("fly_through")
		elif self.phase == "fly_through":
			centre, right, up, caption_distance = self.animation.caption_frame()
			progress = min(1.0, self.phase_seconds / self.fly_through_seconds)
			self.animation.camera_advance = (caption_distance + self.fly_through_overshoot) * ease_in_out(progress)
			if progress >= 1.0:
				self._enter("cassette")
				self.cassette_animation.restart()

		self.animation.draw()
		if self.phase != "caption":
			centre, right, up, _ = self.animation.caption_frame()
			below = self.computer.key_pitch / 2 + self.presents_gap + self.presents_height / 2
			self.presents_label.draw(tuple(c - below * u for c, u in zip(centre, up)), right, up)

	def _cassette_step(self, seconds):
		self.cassette_animation.update(seconds)
		self.cassette_animation.draw()
		if self.cassette_animation.done:
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
