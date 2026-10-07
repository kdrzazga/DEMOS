"""Viewer for CassetteIntoDatasette - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.c64.datasette.cassette_into_datasette_viewer

or directly as a script (python demos\\c64\\datasette\\cassette_into_datasette_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.datasette.cassette import Cassette
from demos.c64.datasette.cassette_into_datasette import CassetteIntoDatasette
from demos.c64.datasette.datasette import Datasette
from demos.c64.scene import setup_scene


class CassetteIntoDatasetteViewer(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.replay_after_seconds = 1.5
		self.seconds_since_done = 0.0
		super().__init__(1280, 800, "Cassette into Datasette", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		aspect = self.width / self.height
		setup_scene(aspect, self.fov, self.background)

		self.datasette = Datasette()
		self.datasette.build()
		self.cassette = Cassette()
		self.cassette.build()
		self.animation = CassetteIntoDatasette(self.datasette, self.cassette, aspect, self.fov)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self.animation.restart()
			self.seconds_since_done = 0.0

	def step(self):
		seconds = 1.0 / self.fps
		self.animation.update(seconds)
		if self.animation.done:
			self.seconds_since_done += seconds
			if self.seconds_since_done >= self.replay_after_seconds:
				self.animation.restart()
				self.seconds_since_done = 0.0
		pygame.display.set_caption(f"{self.title} - {self.animation.phase} - "
		                           f"roll position {self.cassette.roll_position:5.2f} min")

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.animation.draw()


if __name__ == "__main__":
	info = ("The cassette arrives, spins, super fast-forwards and rewinds, moves to the corner;"
		+ "\nthe Datasette arrives and sways, the lid opens, the cassette goes in, the lid closes,"
		+ "\n'press play on tape' is heard and PLAY is pressed. It replays on its own."
		+ "\nSPACE restarts. ESC quits.")

	print(info)

	CassetteIntoDatasetteViewer(windowed=True).run()
