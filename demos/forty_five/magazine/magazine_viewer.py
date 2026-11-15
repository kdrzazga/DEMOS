"""Magazine 3D model viewer - pygame + OpenGL.

Run from the DEMOS project root:

    python -m demos.forty_five.magazine.magazine_viewer          (Komoda issue 1)
    python -m demos.forty_five.magazine.magazine_viewer kna      (K&A Plus issue 1)

or directly as a script (python demos\\c64\\magazine\\magazine_viewer.py).
"""

import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.forty_five.magazine.kna_plus import KnA_Plus
from demos.forty_five.magazine.komoda_01 import Komoda_01
from demos.forty_five.orbit_viewer import OrbitViewer


class MagazineViewer(OrbitViewer):

	def __init__(self, magazine_class=Komoda_01, windowed=False, triggered=False):
		self.magazine_class = magazine_class
		self.configure_orbit(yaw=0.0, pitch=50.0, distance=70.0, min_distance=20.0, max_distance=200.0)
		self.light_direction = (-0.3, 1.0, 0.6, 0.0)
		self.idle_spin_degrees = 0.0
		self.forward_keys = (pygame.K_RIGHT, pygame.K_SPACE, pygame.K_PAGEDOWN)
		self.back_keys = (pygame.K_LEFT, pygame.K_BACKSPACE, pygame.K_PAGEUP)
		super().__init__("Magazine", windowed=windowed, triggered=triggered)

	def build_model(self):
		self.magazine = self.magazine_class()
		self.magazine.build()

	def handle_model_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in self.forward_keys:
			self.magazine.turn_page()
		elif event.type == pygame.KEYDOWN and event.key in self.back_keys:
			self.magazine.turn_back()

	def update_model(self):
		self.magazine.update(1.0 / self.fps)
		left, right = self.magazine.visible_pages()
		shown = " - ".join(str(page) for page in (left, right) if page is not None)
		pygame.display.set_caption(f"{self.title} - page {shown} / {self.magazine.page_count}")

	def draw_model(self):
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
