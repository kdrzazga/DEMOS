import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.c64breadbox.c64_board import C64Board
from demos.c64.c64breadbox.layout import BoardLayoutFactory
from demos.c64.scene import setup_scene


class C64BoardTest(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.field_of_view_degrees = 40.0
		self.background_color = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.default_view = (0.0, 50.0, 55.0)
		self.top_view = (0.0, 90.0, 50.0)
		self.yaw, self.pitch, self.distance = self.default_view
		self.min_distance, self.max_distance = 8.0, 150.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.1
		self.idle_frames_before_spin = 300
		self.frames_since_drag = 0
		self.show_seat_markers = False
		self.show_socket_names = False
		super().__init__(1280, 800, "C64 Board ASSY 250425", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		setup_scene(self.width / self.height, self.field_of_view_degrees, self.background_color)
		self.board = C64Board(BoardLayoutFactory.create_assy_250425())
		self.board.build()

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN:
			self._handle_key(event.key)
		elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
			delta_x, delta_y = event.rel
			self.yaw += delta_x * self.drag_degrees_per_pixel
			self.pitch = max(-89.0, min(90.0, self.pitch + delta_y * self.drag_degrees_per_pixel))
			self.frames_since_drag = 0
		elif event.type == pygame.MOUSEWHEEL:
			self.distance = max(self.min_distance, min(self.max_distance, self.distance * (0.9 ** event.y)))

	def _handle_key(self, key):
		if key == pygame.K_s:
			self.show_seat_markers = not self.show_seat_markers
		elif key == pygame.K_n:
			self.show_socket_names = not self.show_socket_names
		elif key == pygame.K_t:
			self._set_view(self.top_view)
		elif key == pygame.K_HOME:
			self._set_view(self.default_view)

	def _set_view(self, view):
		self.yaw, self.pitch, self.distance = view
		self.frames_since_drag = 0

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

		self.board.draw()
		if self.show_seat_markers:
			self.board.draw_seat_markers()
		if self.show_socket_names:
			self.board.draw_socket_names()


if __name__ == "__main__":
	print("Drag with the left mouse button to orbit, mouse wheel to zoom."
	      + "\nS: seat markers (red = pin 1, yellow = contacts, cyan = insertion axis)."
	      + "\nN: socket names.  T: top view.  Home: reset view."
	      + "\nThe board spins slowly after a few seconds without dragging."
	      + "\nESC / window-close quits.")
	arguments = [argument.lower() for argument in sys.argv[1:]]
	C64BoardTest(windowed=not any(argument in ("f", "full", "fullscreen") for argument in arguments)).run()
