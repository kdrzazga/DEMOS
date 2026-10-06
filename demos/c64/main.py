"""Commodore 64 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.c64.main

"""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.pygame_demo import PygameDemo

try:
	from commodore64 import Commodore64
except ModuleNotFoundError:
	from demos.c64.commodore64 import Commodore64


class C64Viewer(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.yaw = -20.0
		self.pitch = 32.0
		self.distance = 62.0
		self.min_distance, self.max_distance = 20.0, 140.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.15
		self.idle_frames_before_spin = 180
		self.frames_since_drag = 0
		super().__init__(1280, 800, "Commodore 64", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)

		glClearColor(*self.background, 1.0)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_NORMALIZE)
		glShadeModel(GL_SMOOTH)

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
		glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
		glLightfv(GL_LIGHT0, GL_AMBIENT, (0.38, 0.38, 0.38, 1.0))
		glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.75, 0.75, 0.72, 1.0))
		glLightfv(GL_LIGHT0, GL_SPECULAR, (0.15, 0.15, 0.15, 1.0))
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.3, 0.3, 0.3, 1.0))
		glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 24.0)

		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.fov, self.width / self.height, 1.0, 400.0)
		glMatrixMode(GL_MODELVIEW)

		self.computer = Commodore64()
		self.computer.build()

	def handle_event(self, event):
		if event.type in (pygame.KEYDOWN, pygame.KEYUP):
			self.computer.press(event.key, event.type == pygame.KEYDOWN)
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
		glTranslatef(0.0, -2.8, 0.0)

		self.computer.update()
		self.computer.draw()


if __name__ == "__main__":
	info = ("Drag with the left mouse button to orbit, mouse wheel to zoom.\nTyping on the PC "
		+ "keyboard presses the matching C64 keys (positional mapping, see keys.py). "
		+ "\nThe model spins slowly on its own after a few seconds without dragging. "
		+ "\nESC / window-close quits.")

	print(info)

	C64Viewer(windowed=True).run()
