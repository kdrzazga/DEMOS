"""Compact cassette 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.c64.datasette.cassette_viewer

or directly as a script (python demos\\c64\\datasette\\cassette_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.datasette.cassette import Cassette
from demos.c64.scene import setup_scene


class CassetteViewer(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.yaw = -15.0
		self.pitch = 45.0
		self.distance = 20.0
		self.min_distance, self.max_distance = 6.0, 80.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.15
		self.idle_frames_before_spin = 180
		self.frames_since_drag = 0
		self.play_minutes_per_second = 1 / 15
		self.wind_minutes_per_second = 1.0
		self.playing = False
		self.held_wind = 0
		super().__init__(1280, 800, "Compact cassette", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		setup_scene(self.width / self.height, self.fov, self.background)

		self.cassette = Cassette()
		self.cassette.build()

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
			self.playing = not self.playing
		elif event.type in (pygame.KEYDOWN, pygame.KEYUP) and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
			direction = -1 if event.key == pygame.K_LEFT else 1
			self.held_wind = direction if event.type == pygame.KEYDOWN else 0
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
		if self.held_wind:
			self.cassette.wind(self.held_wind * self.wind_minutes_per_second / self.fps)
		elif self.playing:
			self.cassette.wind(self.play_minutes_per_second / self.fps)
		pygame.display.set_caption(f"{self.title} - roll position {self.cassette.roll_position:5.2f} / "
		                           f"{self.cassette.length_minutes:g} min")

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.distance)
		glRotatef(self.pitch, 1.0, 0.0, 0.0)
		glRotatef(self.yaw, 0.0, 1.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
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
