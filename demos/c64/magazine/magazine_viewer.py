"""Magazine 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.c64.magazine.magazine_viewer          (Komoda issue 1)
    python -m demos.c64.magazine.magazine_viewer kna      (K&A Plus issue 1)

or directly as a script (python demos\\c64\\magazine\\magazine_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.magazine.kna_plus import KnA_Plus
from demos.c64.magazine.komoda_01 import Komoda_01
from demos.c64.scene import setup_scene


class MagazineViewer(PygameDemo):

	def __init__(self, magazine_class=Komoda_01, windowed=False, triggered=False):
		self.magazine_class = magazine_class
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.light_direction = (-0.3, 1.0, 0.6, 0.0)
		self.yaw = 0.0
		self.pitch = 50.0
		self.distance = 70.0
		self.min_distance, self.max_distance = 20.0, 200.0
		self.drag_degrees_per_pixel = 0.35
		self.forward_keys = (pygame.K_RIGHT, pygame.K_SPACE, pygame.K_PAGEDOWN)
		self.back_keys = (pygame.K_LEFT, pygame.K_BACKSPACE, pygame.K_PAGEUP)
		super().__init__(1280, 800, "Magazine", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		setup_scene(self.width / self.height, self.fov, self.background)

		self.magazine = self.magazine_class()
		self.magazine.build()

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in self.forward_keys:
			self.magazine.turn_page()
		elif event.type == pygame.KEYDOWN and event.key in self.back_keys:
			self.magazine.turn_back()
		elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
			delta_x, delta_y = event.rel
			self.yaw += delta_x * self.drag_degrees_per_pixel
			self.pitch = max(-89.0, min(89.0, self.pitch + delta_y * self.drag_degrees_per_pixel))
		elif event.type == pygame.MOUSEWHEEL:
			self.distance = max(self.min_distance, min(self.max_distance, self.distance * (0.9 ** event.y)))

	def step(self):
		self.magazine.update(1.0 / self.fps)
		left, right = self.magazine.visible_pages()
		shown = " - ".join(str(page) for page in (left, right) if page is not None)
		pygame.display.set_caption(f"{self.title} - page {shown} / {self.magazine.page_count}")

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.distance)
		glRotatef(self.pitch, 1.0, 0.0, 0.0)
		glRotatef(self.yaw, 0.0, 1.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		glTranslatef(-self.magazine.centre_x(), 0.0, 0.0)

		self.magazine.draw()


if __name__ == "__main__":
	info = ("RIGHT / SPACE / PAGE DOWN: turn the page, LEFT / BACKSPACE / PAGE UP: turn back."
		+ "\nDrag with the left mouse button to orbit, mouse wheel to zoom."
		+ "\nThe window title shows the open pages."
		+ "\nESC / window-close quits.")

	print(info)

	magazine_class = KnA_Plus if "kna" in sys.argv[1:] else Komoda_01
	MagazineViewer(magazine_class, windowed=True).run()
