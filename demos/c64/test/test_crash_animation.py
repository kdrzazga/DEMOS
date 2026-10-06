"""Plays CrashAnimation on a loop.

Run from the DEMOS project root:

    python -m demos.c64.test.test_crash_animation

SPACE replays at once, otherwise it replays a second after it ends.
ESC / window-close quits.
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__))))))

from demos.c64.crash_animation import CrashAnimation
from demos.c64.main import C64Viewer


class CrashAnimationTest(C64Viewer):

	def __init__(self, windowed=False, triggered=False):
		self.replay_delay_frames = 60
		self.frames_since_done = 0
		super().__init__(windowed=windowed, triggered=triggered)

	def setup(self):
		super().setup()
		self.animation = self._make_animation()

	def _make_animation(self):
		return CrashAnimation(self.computer, self.width / self.height, self.fov, fps=self.fps)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self._replay()

	def _replay(self):
		self.frames_since_done = 0
		self.animation.restart()

	def step(self):
		if self.animation.done:
			self.frames_since_done += 1
			if self.frames_since_done > self.replay_delay_frames:
				self._replay()

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.animation.update()
		self.animation.draw()


if __name__ == "__main__":
	CrashAnimationTest(windowed=True).run()
