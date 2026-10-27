import math
import os

import pygame
from OpenGL.GL import *

from demos.c64.laser_line import LaserLine


def smooth_step(progress):
	return progress * progress * (3.0 - 2.0 * progress)


class PictureTexture:

	def __init__(self, image_path):
		self.image_path = image_path
		surface = pygame.image.load(image_path).convert_alpha()
		self.pixel_width, self.pixel_height = surface.get_size()
		self.aspect_ratio = self.pixel_width / self.pixel_height
		self.texture_id = self._upload_surface_as_texture(surface)

	@staticmethod
	def _upload_surface_as_texture(surface):
		width, height = surface.get_size()
		rgba_bytes_bottom_row_first = pygame.image.tobytes(surface, "RGBA", True)
		texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             rgba_bytes_bottom_row_first)
		return texture_id

	def draw_vertical_strip(self, left_edge_fraction, right_edge_fraction, picture_width, picture_height):
		if right_edge_fraction <= left_edge_fraction:
			return
		half_height = picture_height / 2
		left_x = (left_edge_fraction - 0.5) * picture_width
		right_x = (right_edge_fraction - 0.5) * picture_width
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glBegin(GL_QUADS)
		glTexCoord2f(left_edge_fraction, 0.0)
		glVertex3f(left_x, -half_height, 0.0)
		glTexCoord2f(right_edge_fraction, 0.0)
		glVertex3f(right_x, -half_height, 0.0)
		glTexCoord2f(right_edge_fraction, 1.0)
		glVertex3f(right_x, half_height, 0.0)
		glTexCoord2f(left_edge_fraction, 1.0)
		glVertex3f(left_x, half_height, 0.0)
		glEnd()

	def destroy(self):
		glDeleteTextures([self.texture_id])


class LaserSweepSegment:

	def __init__(self, start_position_fraction, end_position_fraction, start_second, duration_seconds):
		self.start_position_fraction = start_position_fraction
		self.end_position_fraction = end_position_fraction
		self.start_second = start_second
		self.duration_seconds = duration_seconds

	@property
	def end_second(self):
		return self.start_second + self.duration_seconds

	@property
	def movement_direction(self):
		return math.copysign(1.0, self.end_position_fraction - self.start_position_fraction)

	def position_at(self, elapsed_seconds):
		progress = min(1.0, max(0.0, (elapsed_seconds - self.start_second) / self.duration_seconds))
		travelled = (self.end_position_fraction - self.start_position_fraction) * smooth_step(progress)
		return self.start_position_fraction + travelled


class LaserSweepPath:

	def __init__(self, signed_moves_in_picture_widths, sweep_speed_in_picture_widths_per_second,
	             shortest_move_seconds=0.2):
		self.sweep_speed_in_picture_widths_per_second = sweep_speed_in_picture_widths_per_second
		self.shortest_move_seconds = shortest_move_seconds
		self.segments = self._build_segments(signed_moves_in_picture_widths)
		self.total_seconds = self.segments[-1].end_second

	def _build_segments(self, signed_moves_in_picture_widths):
		segments = []
		position_fraction = 0.0
		start_second = 0.0
		for signed_move in signed_moves_in_picture_widths:
			end_position_fraction = min(1.0, max(0.0, position_fraction + signed_move))
			duration_seconds = max(self.shortest_move_seconds,
			                       abs(signed_move) / self.sweep_speed_in_picture_widths_per_second)
			segments.append(LaserSweepSegment(position_fraction, end_position_fraction, start_second, duration_seconds))
			position_fraction = end_position_fraction
			start_second += duration_seconds
		return segments

	def _segment_at(self, elapsed_seconds):
		for segment in self.segments:
			if elapsed_seconds < segment.end_second:
				return segment
		return None

	def position_at(self, elapsed_seconds):
		segment = self._segment_at(elapsed_seconds)
		if segment is None:
			return self.segments[-1].end_position_fraction
		return segment.position_at(elapsed_seconds)

	def movement_direction_at(self, elapsed_seconds):
		segment = self._segment_at(elapsed_seconds)
		return 0.0 if segment is None else segment.movement_direction

	def is_finished_at(self, elapsed_seconds):
		return elapsed_seconds >= self.total_seconds


class PictureTransition:

	def __init__(self, outgoing_picture, incoming_picture, laser_sweep_path):
		self.outgoing_picture = outgoing_picture
		self.incoming_picture = incoming_picture
		self.laser_sweep_path = laser_sweep_path
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def laser_position_fraction(self):
		return self.laser_sweep_path.position_at(self.elapsed_seconds)

	@property
	def laser_movement_direction(self):
		return self.laser_sweep_path.movement_direction_at(self.elapsed_seconds)

	@property
	def finished(self):
		return self.laser_sweep_path.is_finished_at(self.elapsed_seconds)

	def draw_pictures_split_at_laser(self, picture_width, picture_height):
		laser_position_fraction = self.laser_position_fraction
		self.incoming_picture.draw_vertical_strip(0.0, laser_position_fraction, picture_width, picture_height)
		self.outgoing_picture.draw_vertical_strip(laser_position_fraction, 1.0, picture_width, picture_height)


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
