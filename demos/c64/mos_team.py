import math
import os

from OpenGL.GL import *

from lib.laser_line import LaserLine, LaserSweepPath, PictureTexture, PictureTransition


class MosTeam:

	def __init__(self, aspect_ratio, field_of_view_degrees, picture_directory=None,
	             picture_file_names=("MOS.png", "MOS2.png", "MOS3.png", "MOS4.png"), picture_height=10.0,
	             screen_fill_fraction=0.8, opening_hold_seconds=1.0, hold_seconds_between_transitions=1.5,
	             closing_hold_seconds=2.0,
	             laser_signed_moves_in_picture_widths=(0.40, -0.25, 0.45, -0.30, 0.30, -0.05, 0.40, -0.10, 0.15),
	             laser_sweep_speed_in_picture_widths_per_second=0.45, sway_yaw_amplitude_degrees=14.0,
	             sway_pitch_amplitude_degrees=5.0, sway_period_seconds=9.0):
		self.aspect_ratio = aspect_ratio
		self.field_of_view_degrees = field_of_view_degrees
		self.picture_directory = picture_directory or os.path.join(
			os.path.dirname(os.path.abspath(__file__)), "resources", "history", "mos")
		self.picture_height = picture_height
		self.screen_fill_fraction = screen_fill_fraction
		self.opening_hold_seconds = opening_hold_seconds
		self.hold_seconds_between_transitions = hold_seconds_between_transitions
		self.closing_hold_seconds = closing_hold_seconds
		self.laser_signed_moves_in_picture_widths = laser_signed_moves_in_picture_widths
		self.laser_sweep_speed_in_picture_widths_per_second = laser_sweep_speed_in_picture_widths_per_second
		self.sway_yaw_amplitude_degrees = sway_yaw_amplitude_degrees
		self.sway_pitch_amplitude_degrees = sway_pitch_amplitude_degrees
		self.sway_period_seconds = sway_period_seconds

		self.pictures = [PictureTexture(os.path.join(self.picture_directory, file_name))
		                 for file_name in picture_file_names]
		self.picture_width = picture_height * self.pictures[0].aspect_ratio
		self.camera_distance = self._camera_distance_that_fits_picture_on_screen()
		self.laser_line = LaserLine(surface_top_y=picture_height / 2, surface_bottom_y=-picture_height / 2)
		self.restart()

	def _camera_distance_that_fits_picture_on_screen(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.field_of_view_degrees) / 2)
		horizontal_half_angle_tangent = vertical_half_angle_tangent * self.aspect_ratio
		distance_fitting_height = self.picture_height / 2 / self.screen_fill_fraction / vertical_half_angle_tangent
		distance_fitting_width = self.picture_width / 2 / self.screen_fill_fraction / horizontal_half_angle_tangent
		return max(distance_fitting_height, distance_fitting_width)

	def restart(self):
		self.total_elapsed_seconds = 0.0
		self.shown_picture_index = 0
		self.active_transition = None
		self.remaining_hold_seconds = self.opening_hold_seconds
		self.finished = False
		self.laser_line.reset()

	@property
	def done(self):
		return self.finished

	@property
	def is_showing_last_picture(self):
		return self.shown_picture_index >= len(self.pictures) - 1

	def update(self, seconds):
		self.total_elapsed_seconds += seconds
		if self.active_transition is not None:
			self._advance_active_transition(seconds)
		elif not self.finished:
			self._advance_hold(seconds)
		self.laser_line.update(seconds)

	def _advance_active_transition(self, seconds):
		self.active_transition.update(seconds)
		self._move_laser_line_to_transition_position()
		if self.active_transition.finished:
			self.active_transition = None
			self.laser_line.switch_off()
			self.shown_picture_index += 1
			self.remaining_hold_seconds = (self.closing_hold_seconds if self.is_showing_last_picture
			                               else self.hold_seconds_between_transitions)

	def _advance_hold(self, seconds):
		self.remaining_hold_seconds -= seconds
		if self.remaining_hold_seconds > 0.0:
			return
		if self.is_showing_last_picture:
			self.finished = True
		else:
			self._start_transition_to_next_picture()

	def _start_transition_to_next_picture(self):
		laser_sweep_path = LaserSweepPath(self.laser_signed_moves_in_picture_widths,
		                                  self.laser_sweep_speed_in_picture_widths_per_second)
		self.active_transition = PictureTransition(self.pictures[self.shown_picture_index],
		                                           self.pictures[self.shown_picture_index + 1], laser_sweep_path)
		self._move_laser_line_to_transition_position()
		self.laser_line.switch_on()

	def _move_laser_line_to_transition_position(self):
		laser_x = (self.active_transition.laser_position_fraction - 0.5) * self.picture_width
		self.laser_line.move_to(laser_x, self.active_transition.laser_movement_direction)

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self._apply_camera_and_sway()
		self._draw_pictures()
		self.laser_line.draw()
		glPopMatrix()
		glPopAttrib()

	def _apply_camera_and_sway(self):
		sway_angle = 2 * math.pi * self.total_elapsed_seconds / self.sway_period_seconds
		glTranslatef(0.0, 0.0, -self.camera_distance)
		glRotatef(self.sway_yaw_amplitude_degrees * math.sin(sway_angle), 0.0, 1.0, 0.0)
		glRotatef(self.sway_pitch_amplitude_degrees * math.sin(sway_angle * 0.7), 1.0, 0.0, 0.0)

	def _draw_pictures(self):
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		if self.active_transition is not None:
			self.active_transition.draw_pictures_split_at_laser(self.picture_width, self.picture_height)
		else:
			self.pictures[self.shown_picture_index].draw_vertical_strip(0.0, 1.0, self.picture_width,
			                                                            self.picture_height)
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		for picture in self.pictures:
			picture.destroy()
		self.pictures = []
