"""Commodore 64 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.forty_five.c64c.main

"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.forty_five.c64c.commodore64 import Commodore64
from demos.forty_five.orbit_viewer import OrbitViewer


class C64Viewer(OrbitViewer):

	def __init__(self, windowed=False, triggered=False):
		self.configure_orbit(yaw=-20.0, pitch=32.0, distance=62.0, min_distance=20.0, max_distance=140.0)
		super().__init__("Commodore 64", windowed=windowed, triggered=triggered)

	def build_model(self):
		self.computer = Commodore64()
		self.computer.build()

	def handle_model_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			self.computer.press(event.key, event.type == pygame.KEYDOWN)

	def update_model(self):
		self.computer.update()

	def draw_model(self):
		glTranslatef(0.0, -2.8, 0.0)
		self.computer.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit, mouse wheel to zoom.\nTyping on the PC "
		+ "keyboard presses the matching C64 keys (positional mapping, see keys.py). "
		+ "\nThe model spins slowly on its own after a few seconds without dragging. "
		+ "\nESC / window-close quits.")

	print(info)

	C64Viewer(windowed=True).run()
