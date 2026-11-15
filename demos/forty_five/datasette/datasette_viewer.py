"""Commodore Datasette 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.forty_five.datasette.datasette_viewer

or directly as a script (python demos\\c64\\datasette\\datasette_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.forty_five.datasette.datasette import Datasette
from demos.forty_five.orbit_viewer import OrbitViewer


class DatasetteViewer(OrbitViewer):

	def __init__(self, windowed=False, triggered=False):
		self.configure_orbit(yaw=-25.0, pitch=30.0, distance=42.0, min_distance=12.0, max_distance=120.0)
		super().__init__("Commodore Datasette", windowed=windowed, triggered=triggered)

	def build_model(self):
		self.datasette = Datasette()
		self.datasette.build()

	def handle_model_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			self.datasette.press(event.key, event.type == pygame.KEYDOWN)

	def update_model(self):
		self.datasette.update()

	def draw_model(self):
		glTranslatef(2.0, -1.9, 2.0)
		self.datasette.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit, mouse wheel to zoom."
		+ "\n1-6 (or F1-F6): RECORD, PLAY, REWIND, F.FWD, STOP, EJECT. EJECT while stopped opens / closes the door."
		+ "\nR (or 0): counter reset button."
		+ "\nThe model spins slowly on its own after a few seconds without dragging."
		+ "\nESC / window-close quits.")

	print(info)

	DatasetteViewer(windowed=True).run()
