import math

import numpy as np

from demos.forty_five.rotation import slerp_rotation
from lib.laser_line import smooth_step

LABEL_FACING_VIEWER = np.array(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))


def clamp_progress(value):
	return max(0.0, min(1.0, value))


class ChipInsertion:

	def __init__(self, chip, seat, camera, parked_view_fraction, parked_depth_cm=45.0, showcase_depth_cm=12.0,
	             delay_seconds=0.0, zoom_seconds=1.0, show_seconds=1.8, travel_seconds=1.6, press_seconds=0.45,
	             hover_height_cm=2.5, arc_height_cm=4.0):
		if not chip.fits(seat):
			raise ValueError(f"{type(chip).__name__} ({chip.package.pin_count} pins) does not fit socket {seat.name}")
		self.chip = chip
		self.seat = seat
		self.camera = camera
		self.parked_view_fraction = parked_view_fraction
		self.parked_depth = parked_depth_cm
		self.showcase_depth = showcase_depth_cm
		self.delay_seconds = delay_seconds
		self.zoom_seconds = zoom_seconds
		self.show_seconds = show_seconds
		self.travel_seconds = travel_seconds
		self.press_seconds = press_seconds
		self.hover_height = hover_height_cm
		self.arc_height = arc_height_cm
		self.elapsed_seconds = 0.0
		self.restart()

	@property
	def duration_seconds(self):
		return self.zoom_seconds + self.show_seconds + self.travel_seconds + self.press_seconds

	@property
	def done(self):
		return self.elapsed_seconds >= self.delay_seconds + self.duration_seconds

	def restart(self):
		self.elapsed_seconds = 0.0
		self._apply_pose()

	def finish(self):
		self.elapsed_seconds = self.delay_seconds + self.duration_seconds
		self._apply_pose()

	def update(self, seconds):
		self.elapsed_seconds += seconds
		self._apply_pose()

	def _parked_eye_position(self):
		fraction_x, fraction_y = self.parked_view_fraction
		return self.camera.view_point(fraction_x, fraction_y, self.parked_depth)

	def _showcase_eye_position(self):
		return self.camera.view_point(0.0, 0.0, self.showcase_depth)

	def _hover_pose(self):
		seated_position, seated_rotation = self.chip.seated_pose(self.seat)
		return seated_position + np.array((0.0, self.hover_height, 0.0)), seated_rotation

	def _apply_pose(self):
		active_seconds = self.elapsed_seconds - self.delay_seconds
		zoom_end = self.zoom_seconds
		show_end = zoom_end + self.show_seconds
		travel_end = show_end + self.travel_seconds
		if active_seconds < zoom_end:
			progress = smooth_step(clamp_progress(active_seconds / self.zoom_seconds))
			parked, showcase = self._parked_eye_position(), self._showcase_eye_position()
			self.chip.set_pose(*self.camera.eye_to_world(parked + (showcase - parked) * progress, LABEL_FACING_VIEWER))
		elif active_seconds < show_end:
			self.chip.set_pose(*self.camera.eye_to_world(self._showcase_eye_position(), LABEL_FACING_VIEWER))
		elif active_seconds < travel_end:
			progress = smooth_step(clamp_progress((active_seconds - show_end) / self.travel_seconds))
			start_position, start_rotation = self.camera.eye_to_world(self._showcase_eye_position(), LABEL_FACING_VIEWER)
			hover_position, hover_rotation = self._hover_pose()
			position = start_position + (hover_position - start_position) * progress
			position[1] += math.sin(math.pi * progress) * self.arc_height
			self.chip.set_pose(position, slerp_rotation(start_rotation, hover_rotation, progress))
		else:
			progress = smooth_step(clamp_progress((active_seconds - travel_end) / self.press_seconds))
			hover_position, rotation = self._hover_pose()
			seated_position, _ = self.chip.seated_pose(self.seat)
			self.chip.set_pose(hover_position + (seated_position - hover_position) * progress, rotation)
