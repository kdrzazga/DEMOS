"""Joystick 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.forty_five.joystick.joystick_viewer

or directly as a script (python demos\\c64\\joystick\\joystick_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.forty_five.joystick.joystick import Joystick
from demos.forty_five.orbit_viewer import OrbitViewer


class JoystickViewer(OrbitViewer):

	def __init__(self, windowed=False, triggered=False):
		self.configure_orbit(yaw=-30.0, pitch=18.0, distance=48.0, min_distance=12.0, max_distance=120.0)
		super().__init__("Joystick", windowed=windowed, triggered=triggered)

	def build_model(self):
		self.joystick = Joystick()
		self.joystick.build()

	def handle_model_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			self.joystick.press(event.key, event.type == pygame.KEYDOWN)

	def update_model(self):
		self.joystick.update()

	def draw_model(self):
		glTranslatef(-3.0, -6.5, 0.0)
		self.joystick.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit, mouse wheel to zoom."
		+ "\nArrow keys tilt the stick. SPACE: trigger, CTRL / ENTER: top button."
		+ "\nThe model spins slowly on its own after a few seconds without dragging."
		+ "\nESC / window-close quits.")

	print(info)

	JoystickViewer(windowed=True).run()
