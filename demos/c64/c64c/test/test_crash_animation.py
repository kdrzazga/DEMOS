"""Plays the iny.mp4 intro once, then CrashAnimation on a loop.

Run from the DEMOS project root:

    python -m demos.c64.c64c.test.test_crash_animation

SPACE skips the intro; after it, SPACE replays the animation at once, otherwise
it replays a second after it ends. ESC / window-close quits.
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from demos.c64.c64c.crash_animation import CrashAnimation
from demos.c64.c64c.main import C64Viewer
from demos.c64.intro import IntroVideo

RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources")


class CrashAnimationTest(C64Viewer):

	def __init__(self, windowed=False, triggered=False, play_intro=True):
		self.replay_delay_frames = 60
		self.frames_since_done = 0
		self.play_intro = play_intro
		super().__init__(windowed=windowed, triggered=triggered)

	def setup(self):
		super().setup()
		self.animation = self._make_animation()
		self.intro = None
		if self.play_intro:
			self.intro = IntroVideo(os.path.join(RESOURCES, "iny.mp4"), os.path.join(RESOURCES, "iny.wav"),
			                        self.width / self.height)

	def _make_animation(self):
		return CrashAnimation(self.computer, self.width / self.height, self.fov, fps=self.fps)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			if self.intro:
				self._end_intro()
			else:
				self._replay()

	def _end_intro(self):
		self.intro.destroy()
		self.intro = None

	def _replay(self):
		self.frames_since_done = 0
		self.animation.restart()

	def step(self):
		if self.intro:
			self.intro.render()
			if self.intro.done:
				self._end_intro()
			return

		if self.animation.done:
			self.frames_since_done += 1
			if self.frames_since_done > self.replay_delay_frames:
				self._replay()

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.animation.update()
		self.animation.draw()


if __name__ == "__main__":
	CrashAnimationTest(windowed=True).run()
