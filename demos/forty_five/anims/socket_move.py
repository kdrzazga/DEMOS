import math

import numpy as np

from lib.laser_line import smooth_step
from demos.forty_five.rotation import slerp_rotation


class SocketMove:

	def __init__(self, chip_animation, board_arrival, socket_name):
		self.chip_animation = chip_animation
		self.board_arrival = board_arrival
		self.seat = board_arrival.seat(socket_name)
		if not chip_animation.chip.fits(self.seat):
			raise ValueError(f"{chip_animation.chip.label} does not fit socket {socket_name}")
		self.travel_seconds = 1.6
		self.press_seconds = 0.45
		self.hover_height_cm = 2.5
		self.arc_height = 4.0
		self.start_transform = None
		self.elapsed_seconds = None

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.travel_seconds + self.press_seconds

	def start(self):
		self.start_transform = self.chip_animation.eye_transform()
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		if not self.started:
			return
		self.elapsed_seconds += seconds
		self.chip_animation.eye_transform_override = self._current_eye_transform()

	def _seated_eye_pose(self):
		return self.board_arrival.eye_transform_of_board_pose(*self.chip_animation.chip.seated_pose(self.seat))

	def _current_eye_transform(self):
		seated_position, seated_rotation = self._seated_eye_pose()
		hover_position = seated_position + self.board_arrival.eye_up_direction * self.hover_height_cm
		if self.elapsed_seconds < self.travel_seconds:
			progress = smooth_step(self.elapsed_seconds / self.travel_seconds)
			start_position, start_rotation, start_scale = self.start_transform
			position = start_position + (hover_position - start_position) * progress
			position = position + np.array((0.0, math.sin(math.pi * progress) * self.arc_height, 0.0))
			scale = math.exp(math.log(start_scale) * (1.0 - progress))
			return position, slerp_rotation(start_rotation, seated_rotation, progress), scale
		press_progress = smooth_step(min(1.0, (self.elapsed_seconds - self.travel_seconds) / self.press_seconds))
		return hover_position + (seated_position - hover_position) * press_progress, seated_rotation, 1.0
