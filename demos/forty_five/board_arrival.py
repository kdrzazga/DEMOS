import math

import numpy as np
from OpenGL.GL import *

from lib.flying_logo import ease_out_cubic
from demos.forty_five.c64breadbox.c64_board import C64Board
from demos.forty_five.c64breadbox.layout import BoardLayoutFactory
from demos.forty_five.rotation import rotation_x


class BoardArrival:

	def __init__(self, field_of_view_degrees):
		self.field_of_view_degrees = field_of_view_degrees
		self.camera_distance = 55.0
		self.pitch_degrees = 50.0
		self.rest_fraction_from_top = 0.62
		self.start_fraction_from_top = 1.9
		self.enter_seconds = 3.0
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.board = C64Board(BoardLayoutFactory.create_assy_250425())
		self.board.build()
		self.elapsed_seconds = None

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def arrived(self):
		return self.started and self.elapsed_seconds >= self.enter_seconds

	def begin(self):
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def _current_fraction_from_top(self):
		progress = ease_out_cubic(min(1.0, self.elapsed_seconds / self.enter_seconds))
		return self.start_fraction_from_top + (self.rest_fraction_from_top - self.start_fraction_from_top) * progress

	def _eye_y_of_board_centre(self):
		visible_height = 2 * self.camera_distance * math.tan(math.radians(self.field_of_view_degrees) / 2)
		return (0.5 - self._current_fraction_from_top()) * visible_height

	def seat(self, socket_name):
		return self.board.seat(socket_name)

	def eye_transform_of_board_pose(self, board_position, board_rotation):
		tilt = rotation_x(self.pitch_degrees)
		board_centre = np.array((0.0, self._eye_y_of_board_centre(), -self.camera_distance))
		return board_centre + tilt @ np.asarray(board_position), tilt @ np.asarray(board_rotation)

	@property
	def eye_up_direction(self):
		return rotation_x(self.pitch_degrees) @ np.array((0.0, 1.0, 0.0))

	def draw(self):
		if not self.started:
			return
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_NORMALIZE)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(0.0, self._eye_y_of_board_centre(), -self.camera_distance)
		glRotatef(self.pitch_degrees, 1.0, 0.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		self.board.draw()
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		self.board.destroy()
