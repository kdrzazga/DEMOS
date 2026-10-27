import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.mos_team import MosTeam
from demos.c64.scene import setup_scene


class MosTeamTest(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.field_of_view_degrees = 40.0
		self.background_color = (0.0, 0.0, 0.0)
		self.replay_delay_seconds = 1.5
		self.seconds_since_animation_finished = 0.0
		super().__init__(1280, 800, "MOS Team", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		aspect_ratio = self.width / self.height
		setup_scene(aspect_ratio, self.field_of_view_degrees, self.background_color)
		self.mos_team = MosTeam(aspect_ratio, self.field_of_view_degrees)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self._replay_animation()

	def _replay_animation(self):
		self.seconds_since_animation_finished = 0.0
		self.mos_team.restart()

	def step(self):
		frame_seconds = 1.0 / self.fps
		if self.mos_team.done:
			self.seconds_since_animation_finished += frame_seconds
			if self.seconds_since_animation_finished >= self.replay_delay_seconds:
				self._replay_animation()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.mos_team.update(frame_seconds)
		self.mos_team.draw()


if __name__ == "__main__":
	arguments = [argument.lower() for argument in sys.argv[1:]]
	MosTeamTest(windowed=not any(argument in ("f", "full", "fullscreen") for argument in arguments)).run()
