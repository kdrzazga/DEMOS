"""Commodore Datasette 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.c64.datasette.datasette_viewer

or directly as a script (python demos\\c64\\datasette\\datasette_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.datasette.datasette import Datasette
from demos.c64.scene import setup_scene


class DatasetteViewer(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.yaw = -25.0
		self.pitch = 30.0
		self.distance = 42.0
		self.min_distance, self.max_distance = 12.0, 120.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.15
		self.idle_frames_before_spin = 180
		self.frames_since_drag = 0
		super().__init__(1280, 800, "Commodore Datasette", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		setup_scene(self.width / self.height, self.fov, self.background)

		self.datasette = Datasette()
		self.datasette.build()

	def handle_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			self.datasette.press(event.key, event.type == pygame.KEYDOWN)
		elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
			delta_x, delta_y = event.rel
			self.yaw += delta_x * self.drag_degrees_per_pixel
			self.pitch = max(-89.0, min(89.0, self.pitch + delta_y * self.drag_degrees_per_pixel))
			self.frames_since_drag = 0
		elif event.type == pygame.MOUSEWHEEL:
			self.distance = max(self.min_distance, min(self.max_distance, self.distance * (0.9 ** event.y)))

	def step(self):
		self.frames_since_drag += 1
		if self.frames_since_drag > self.idle_frames_before_spin:
			self.yaw += self.idle_spin_degrees

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.distance)
		glRotatef(self.pitch, 1.0, 0.0, 0.0)
		glRotatef(self.yaw, 0.0, 1.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		glTranslatef(2.0, -1.9, 2.0)

		self.datasette.update()
		self.datasette.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit, mouse wheel to zoom."
		+ "\n1-6 (or F1-F6): RECORD, PLAY, REWIND, F.FWD, STOP, EJECT. EJECT while stopped opens / closes the door."
		+ "\nR (or 0): counter reset button."
		+ "\nThe model spins slowly on its own after a few seconds without dragging."
		+ "\nESC / window-close quits.")

	print(info)

	DatasetteViewer(windowed=True).run()
