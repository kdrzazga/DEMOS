"""Compact cassette 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.forty_five.datasette.cassette_viewer

or directly as a script (python demos\\c64\\datasette\\cassette_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.forty_five.datasette.cassette import Cassette
from demos.forty_five.orbit_viewer import OrbitViewer


class CassetteViewer(OrbitViewer):

	def __init__(self, windowed=False, triggered=False):
		self.configure_orbit(yaw=-15.0, pitch=45.0, distance=20.0, min_distance=6.0, max_distance=80.0)
		self.play_minutes_per_second = 1 / 15
		self.wind_minutes_per_second = 1.0
		self.playing = False
		self.held_wind = 0
		super().__init__("Compact cassette", windowed=windowed, triggered=triggered)

	def build_model(self):
		self.cassette = Cassette()
		self.cassette.build()

	def handle_model_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self.playing = not self.playing
		elif event.type in (pygame.KEYDOWN, pygame.KEYUP) and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
			direction = -1 if event.key == pygame.K_LEFT else 1
			self.held_wind = direction if event.type == pygame.KEYDOWN else 0

	def update_model(self):
		if self.held_wind:
			self.cassette.wind(self.held_wind * self.wind_minutes_per_second / self.fps)
		elif self.playing:
			self.cassette.wind(self.play_minutes_per_second / self.fps)
		pygame.display.set_caption(f"{self.title} - roll position {self.cassette.roll_position:5.2f} / "
		                           f"{self.cassette.length_minutes:g} min")

	def draw_model(self):
		glTranslatef(0.0, -self.cassette.thickness / 2, 0.0)
		self.cassette.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit (drag up to see side B), mouse wheel to zoom."
		+ "\nSPACE: play / stop, LEFT / RIGHT (held): rewind / fast forward."
		+ "\nThe window title shows the roll position (0 = all tape on the left hub, 60 = all on the right)."
		+ "\nThe model spins slowly on its own after a few seconds without dragging."
		+ "\nESC / window-close quits.")

	print(info)

	CassetteViewer(windowed=True).run()
