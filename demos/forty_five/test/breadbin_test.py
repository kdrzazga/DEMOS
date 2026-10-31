import os
import sys

import pygame
from OpenGL.GL import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.pygame_demo import PygameDemo
from demos.forty_five.c64breadbox.breadbin import Breadbin
from demos.forty_five.c64breadbox.breadbin_merge import BreadbinMerge
from demos.forty_five.c64breadbox.c64_board import C64Board
from demos.forty_five.c64breadbox.layout import BoardLayoutFactory
from demos.forty_five.orbit_camera import OrbitCamera
from demos.forty_five.scene import setup_scene


class BreadbinTest(PygameDemo):

	def __init__(self, windowed=False, triggered=False):
		self.field_of_view_degrees = 40.0
		self.background_color = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.default_view = (-30.0, 35.0, 60.0)
		self.top_view = (0.0, 90.0, 55.0)
		self.right_view = (-90.0, 10.0, 50.0)
		self.back_view = (180.0, 15.0, 55.0)
		self.min_distance, self.max_distance = 8.0, 150.0
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.1
		self.idle_frames_before_spin = 300
		self.frames_since_drag = 0
		self.board_visible = True
		super().__init__(1280, 800, "C64 breadbin", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mouse.set_visible(True)
		aspect_ratio = self.width / self.height
		setup_scene(aspect_ratio, self.field_of_view_degrees, self.background_color)
		self.camera = OrbitCamera(self.field_of_view_degrees, aspect_ratio, *self.default_view)
		board_layout = BoardLayoutFactory.create_assy_250425()
		self.board = C64Board(board_layout)
		self.board.build()
		self.breadbin = Breadbin(board_layout)
		self.breadbin.build()
		self.merge = BreadbinMerge(self.breadbin, board_drops_in=True)

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
		if key == pygame.K_h:
			self.breadbin.top_visible = not self.breadbin.top_visible
		elif key == pygame.K_k:
			self.breadbin.keyboard_visible = not self.breadbin.keyboard_visible
		elif key == pygame.K_b:
			self.board_visible = not self.board_visible
		elif key == pygame.K_t:
			self._set_view(self.top_view)
		elif key == pygame.K_r:
			self._set_view(self.right_view)
		elif key == pygame.K_p:
			self._set_view(self.back_view)
		elif key == pygame.K_HOME:
			self._set_view(self.default_view)
		elif key == pygame.K_SPACE:
			self.merge.restart()

	def _set_view(self, view):
		self.camera.yaw_degrees, self.camera.pitch_degrees, self.camera.distance = view
		self.frames_since_drag = 0

	def step(self):
		self.frames_since_drag += 1
		if self.frames_since_drag > self.idle_frames_before_spin:
			self.camera.yaw_degrees += self.idle_spin_degrees

		if not self.merge.done:
			self.merge.update(1.0 / self.fps)

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply()
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		self.breadbin.draw()
		if self.board_visible:
			glPushMatrix()
			self.breadbin.enter_board_frame()
			self.board.draw()
			glPopMatrix()


if __name__ == "__main__":
	print("Drag with the left mouse button to orbit, mouse wheel to zoom."
	      + "\nH: hide / show the top.  K: hide / show the keyboard.  B: hide / show the board."
	      + "\nSpace: replay the assembly - base, board, keyboard, then the top."
	      + "\nT: top view.  R: right side (ports).  P: back (ports).  Home: reset view."
	      + "\nThe case spins slowly after a few seconds without dragging."
	      + "\nESC / window-close quits.")
	arguments = [argument.lower() for argument in sys.argv[1:]]
	BreadbinTest(windowed=not any(argument in ("f", "full", "fullscreen") for argument in arguments)).run()
