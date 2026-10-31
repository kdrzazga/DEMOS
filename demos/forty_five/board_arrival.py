import math

import numpy as np
from OpenGL.GL import *

from lib.flying_logo import ease_out_cubic
from lib.laser_line import smooth_step
from demos.forty_five.c64breadbox.c64_board import C64Board
from demos.forty_five.c64breadbox.layout import BoardLayoutFactory
from demos.forty_five.chips.mos906114 import MOS906114
from demos.forty_five.chips.ttl74xx import TTL74xx
from demos.forty_five.rotation import rotation_x, rotation_y


class BoardArrival:

	def __init__(self, field_of_view_degrees):
		self.field_of_view_degrees = field_of_view_degrees
		self.camera_distance = 55.0
		self.pitch_degrees = 50.0
		self.rest_fraction_from_top = 0.62
		self.start_fraction_from_top = 1.9
		self.enter_seconds = 3.0
		self.zoomed_camera_distance = 42.0
		self.zoomed_fraction_from_top = 0.5
		self.zoom_seconds = 2.5
		self.spin_seconds = 8.0
		self.sway_pitch_amplitude_degrees = 6.0
		self.sway_period_seconds = 4.0
		self.yaw_sway_amplitude_degrees = 30.0
		self.yaw_sway_seconds = 4.0
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.board = C64Board(BoardLayoutFactory.create_assy_250425())
		self.board.build()
		self.preinstalled_chips = self._preinstall_chips((("PLA", MOS906114()), ("U31", TTL74xx("74LS629", 16))))
		self.elapsed_seconds = None
		self.showcase_elapsed_seconds = None
		self.yaw_sway_elapsed_seconds = None

	def _preinstall_chips(self, socket_names_and_chips):
		for socket_name, chip in socket_names_and_chips:
			seat = self.board.seat(socket_name)
			if not chip.fits(seat):
				raise ValueError(f"{chip.label} does not fit socket {socket_name}")
			chip.build()
			chip.place_in(seat)
		return tuple(chip for _, chip in socket_names_and_chips)

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def arrived(self):
		return self.started and self.elapsed_seconds >= self.enter_seconds

	@property
	def showcase_finished(self):
		return (self.showcase_elapsed_seconds is not None
		        and self.showcase_elapsed_seconds >= self.zoom_seconds + self.spin_seconds)

	@property
	def yaw_sway_finished(self):
		return self.yaw_sway_elapsed_seconds is not None and self.yaw_sway_elapsed_seconds >= self.yaw_sway_seconds

	def begin(self):
		self.elapsed_seconds = 0.0

	def begin_yaw_sway(self):
		self.yaw_sway_elapsed_seconds = 0.0

	def begin_showcase(self):
		self.showcase_elapsed_seconds = 0.0

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds
		if self.showcase_elapsed_seconds is not None:
			self.showcase_elapsed_seconds += seconds
		if self.yaw_sway_elapsed_seconds is not None:
			self.yaw_sway_elapsed_seconds += seconds

	def _zoom_progress(self):
		if self.showcase_elapsed_seconds is None:
			return 0.0
		return smooth_step(min(1.0, self.showcase_elapsed_seconds / self.zoom_seconds))

	def _spin_progress(self):
		if self.showcase_elapsed_seconds is None:
			return 0.0
		spin_seconds_elapsed = self.showcase_elapsed_seconds - self.zoom_seconds
		return smooth_step(min(1.0, max(0.0, spin_seconds_elapsed / self.spin_seconds)))

	def _current_camera_distance(self):
		return self.camera_distance + (self.zoomed_camera_distance - self.camera_distance) * self._zoom_progress()

	def _current_fraction_from_top(self):
		arrival_progress = ease_out_cubic(min(1.0, self.elapsed_seconds / self.enter_seconds))
		arrived_fraction = (self.start_fraction_from_top
		                    + (self.rest_fraction_from_top - self.start_fraction_from_top) * arrival_progress)
		return arrived_fraction + (self.zoomed_fraction_from_top - arrived_fraction) * self._zoom_progress()

	def _sway_pitch_degrees(self):
		if self.showcase_elapsed_seconds is None:
			return 0.0
		sway_angle = 2 * math.pi * self.showcase_elapsed_seconds / self.sway_period_seconds
		return self.sway_pitch_amplitude_degrees * math.sin(sway_angle)

	def _yaw_sway_degrees(self):
		if self.yaw_sway_elapsed_seconds is None:
			return 0.0
		progress = min(1.0, self.yaw_sway_elapsed_seconds / self.yaw_sway_seconds)
		return -self.yaw_sway_amplitude_degrees * math.sin(2 * math.pi * progress)

	def _spin_yaw_degrees(self):
		return 360.0 * self._spin_progress() + self._yaw_sway_degrees()

	def _board_centre_in_eye(self):
		camera_distance = self._current_camera_distance()
		visible_height = 2 * camera_distance * math.tan(math.radians(self.field_of_view_degrees) / 2)
		return np.array((0.0, (0.5 - self._current_fraction_from_top()) * visible_height, -camera_distance))

	def _board_to_eye_rotation(self):
		return rotation_x(self.pitch_degrees + self._sway_pitch_degrees()) @ rotation_y(self._spin_yaw_degrees())

	def seat(self, socket_name):
		return self.board.seat(socket_name)

	def eye_transform_of_board_pose(self, board_position, board_rotation):
		board_to_eye = self._board_to_eye_rotation()
		return (self._board_centre_in_eye() + board_to_eye @ np.asarray(board_position),
		        board_to_eye @ np.asarray(board_rotation))

	@property
	def eye_up_direction(self):
		return self._board_to_eye_rotation() @ np.array((0.0, 1.0, 0.0))

	def draw(self):
		if self.started:
			self.draw_in_board_frame(self._draw_board_with_preinstalled_chips)

	def _draw_board_with_preinstalled_chips(self):
		self.board.draw()
		for chip in self.preinstalled_chips:
			chip.draw()

	def draw_in_board_frame(self, draw_in_frame):
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_NORMALIZE)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(*self._board_centre_in_eye())
		glRotatef(self.pitch_degrees, 1.0, 0.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		glRotatef(self._sway_pitch_degrees(), 1.0, 0.0, 0.0)
		glRotatef(self._spin_yaw_degrees(), 0.0, 1.0, 0.0)
		draw_in_frame()
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		self.board.destroy()
		for chip in self.preinstalled_chips:
			chip.destroy()
