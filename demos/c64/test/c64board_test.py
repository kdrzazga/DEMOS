import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.c64.c64breadbox.c64_board import C64Board
from demos.c64.c64breadbox.layout import BoardLayoutFactory
from demos.c64.chips.chip_insertion import ChipInsertion
from demos.c64.chips.mos65xx import MOS65xx
from demos.c64.chips.mos901xxx import MOS901xxx
from demos.c64.orbit_camera import OrbitCamera
from demos.c64.scene import setup_scene


class C64BoardTest(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.field_of_view_degrees = 40.0
		self.background_color = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.default_view = (0.0, 50.0, 55.0)
		self.top_view = (0.0, 90.0, 50.0)
		self.min_distance, self.max_distance = 8.0, 150.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.1
		self.idle_frames_before_spin = 300
		self.frames_since_drag = 0
		self.show_seat_markers = False
		self.show_socket_names = False
		self.parked_view_fractions = ((-0.8, 0.8), (-0.8, 0.55))
		self.insertions_playing = True
		super().__init__(1280, 800, "C64 Board ASSY 250425", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		aspect_ratio = self.width / self.height
		setup_scene(aspect_ratio, self.field_of_view_degrees, self.background_color)
		self.camera = OrbitCamera(self.field_of_view_degrees, aspect_ratio, *self.default_view)
		self.board = C64Board(BoardLayoutFactory.create_assy_250425())
		self.board.build()
		self.processor = MOS65xx("6510")
		self.basic_rom = MOS901xxx("901226-01")
		self.chips = (self.processor, self.basic_rom)
		for chip in self.chips:
			chip.build()
		processor_insertion = ChipInsertion(self.processor, self.board.seat("CPU"), self.camera,
		                                    self.parked_view_fractions[0])
		basic_rom_insertion = ChipInsertion(self.basic_rom, self.board.seat("ROM_BASIC"), self.camera,
		                                    self.parked_view_fractions[1],
		                                    delay_seconds=processor_insertion.duration_seconds)
		self.insertions = (processor_insertion, basic_rom_insertion)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN:
			self._handle_key(event.key)
		elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
			delta_x, delta_y = event.rel
			self.camera.yaw_degrees += delta_x * self.drag_degrees_per_pixel
			self.camera.pitch_degrees = max(-89.0, min(90.0, self.camera.pitch_degrees + delta_y * self.drag_degrees_per_pixel))
			self.frames_since_drag = 0
		elif event.type == pygame.MOUSEWHEEL:
			self.camera.distance = max(self.min_distance, min(self.max_distance, self.camera.distance * (0.9 ** event.y)))

	def _handle_key(self, key):
		if key == pygame.K_s:
			self.show_seat_markers = not self.show_seat_markers
		elif key == pygame.K_n:
			self.show_socket_names = not self.show_socket_names
		elif key == pygame.K_t:
			self._set_view(self.top_view)
		elif key == pygame.K_HOME:
			self._set_view(self.default_view)
		elif key in (pygame.K_i, pygame.K_SPACE):
			self._restart_insertions(playing=True)
		elif key == pygame.K_r:
			self._restart_insertions(playing=False)

	def _restart_insertions(self, playing):
		self.insertions_playing = playing
		for insertion in self.insertions:
			insertion.restart()

	def _set_view(self, view):
		self.camera.yaw_degrees, self.camera.pitch_degrees, self.camera.distance = view
		self.frames_since_drag = 0

	def step(self):
		self.frames_since_drag += 1
		if self.frames_since_drag > self.idle_frames_before_spin:
			self.camera.yaw_degrees += self.idle_spin_degrees

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply()
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)

		frame_seconds = 1.0 / self.fps if self.insertions_playing else 0.0
		for insertion in self.insertions:
			insertion.update(frame_seconds)
		for chip in self.chips:
			chip.draw()
		self.board.draw()
		if self.show_seat_markers:
			self.board.draw_seat_markers()
		if self.show_socket_names:
			self.board.draw_socket_names()


if __name__ == "__main__":
	print("Drag with the left mouse button to orbit, mouse wheel to zoom."
	      + "\nS: seat markers (red = pin 1, yellow = contacts, cyan = insertion axis)."
	      + "\nN: socket names.  T: top view.  Home: reset view."
	      + "\nI / Space: replay - the 6510, then the BASIC ROM, zoom in, show their labels and go into their sockets."
	      + "\nR: put both chips back in the top-left corner."
	      + "\nThe board spins slowly after a few seconds without dragging."
	      + "\nESC / window-close quits.")
	arguments = [argument.lower() for argument in sys.argv[1:]]
	C64BoardTest(windowed=not any(argument in ("f", "full", "fullscreen") for argument in arguments)).run()
