import math

import numpy as np
from OpenGL.GL import *

from demos.forty_five.c64breadbox.primitives import Box
from demos.forty_five.geometry import color, text_texture, textured_quad
from demos.forty_five.rotation import rotation_y, transform_matrix


def box_between(first_corner, second_corner):
	return Box(tuple(min(pair) for pair in zip(first_corner, second_corner)),
	           tuple(max(pair) for pair in zip(first_corner, second_corner)))


class DilChip:

	def __init__(self, package, label_lines, body_height_cm=0.38, end_clearance_cm=0.05, side_inset_cm=0.08,
	             leg_reach_cm=0.35, leg_exit_height_cm=0.08, leg_thickness_cm=0.025, leg_wide_half_cm=0.075,
	             leg_tip_half_cm=0.025, shoulder_drop_cm=0.05, notch_radius_cm=0.11, dot_radius_cm=0.07,
	             label_end_inset_cm=0.6, label_side_inset_cm=0.1, label_texture_width_px=1024,
	             body_rgb=(28, 28, 30), mark_rgb=(12, 12, 12), leg_rgb=(205, 205, 200), ink_rgb=(205, 205, 205)):
		self.package = package
		self.label_lines = tuple(label_lines)
		self.body_height = body_height_cm
		self.body_half_length = (package.pins_per_side * package.pitch_cm) / 2 + end_clearance_cm
		self.body_half_width = package.row_spacing_cm / 2 - side_inset_cm
		self.leg_reach = leg_reach_cm
		self.leg_exit_height = leg_exit_height_cm
		self.leg_thickness = leg_thickness_cm
		self.leg_wide_half = leg_wide_half_cm
		self.leg_tip_half = leg_tip_half_cm
		self.shoulder_drop = shoulder_drop_cm
		self.notch_radius = notch_radius_cm
		self.dot_radius = dot_radius_cm
		self.label_end_inset = label_end_inset_cm
		self.label_side_inset = label_side_inset_cm
		self.label_texture_width_px = label_texture_width_px
		self.body_rgb = body_rgb
		self.mark_rgb = mark_rgb
		self.leg_rgb = leg_rgb
		self.ink_rgb = ink_rgb
		self.position = np.zeros(3)
		self.rotation = np.identity(3)
		self._label_texture = None
		self._display_list = None

	def fits(self, seat):
		return seat.package == self.package

	def set_label_lines(self, label_lines):
		self.label_lines = tuple(label_lines)
		if self._display_list is not None:
			self.destroy()
			self.build()

	def set_pose(self, position, rotation):
		self.position = np.asarray(position, dtype=float)
		self.rotation = np.asarray(rotation, dtype=float)

	@staticmethod
	def seated_pose(seat):
		centre_x, _, centre_z = seat.centre
		return np.array((centre_x, seat.seat_height, centre_z)), rotation_y(seat.yaw_degrees)

	def place_in(self, seat):
		self.set_pose(*self.seated_pose(seat))

	def build(self):
		self._label_texture = self._make_label_texture()
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_body()
		self._draw_legs()
		self._draw_top_marks()
		glEndList()

	def draw(self):
		glPushMatrix()
		glMultMatrixf(transform_matrix(self.position, self.rotation).T.copy())
		glCallList(self._display_list)
		glPopMatrix()

	def destroy(self):
		glDeleteLists(self._display_list, 1)
		glDeleteTextures([self._label_texture])
		self._display_list = None
		self._label_texture = None

	def _label_size(self):
		return (2 * (self.body_half_length - self.label_end_inset),
		        2 * (self.body_half_width - self.label_side_inset))

	def _make_label_texture(self):
		label_length, label_width = self._label_size()
		width_px = self.label_texture_width_px
		height_px = max(32, round(width_px * label_width / label_length))
		line_count = len(self.label_lines)
		font_px = int(height_px / line_count * 0.7)
		lines = [(text, font_px, self.ink_rgb, (0.5, (index + 0.5) / line_count))
		         for index, text in enumerate(self.label_lines)]
		return text_texture(width_px, height_px, (*self.body_rgb, 255), lines)

	def _draw_body(self):
		Box((-self.body_half_width, 0.0, -self.body_half_length),
		    (self.body_half_width, self.body_height, self.body_half_length)).draw(self.body_rgb)

	def _draw_legs(self):
		shoulder_bottom = self.leg_exit_height
		shoulder_top = shoulder_bottom + self.leg_thickness
		for pin_x, pin_z in self.package.pin_positions():
			side = 1.0 if pin_x > 0 else -1.0
			outer_x = pin_x + side * self.leg_thickness / 2
			inner_x = pin_x - side * self.leg_thickness / 2
			for leg_part in (
					box_between((side * self.body_half_width, shoulder_bottom, pin_z - self.leg_wide_half),
					            (outer_x, shoulder_top, pin_z + self.leg_wide_half)),
					box_between((inner_x, -self.shoulder_drop, pin_z - self.leg_wide_half),
					            (outer_x, shoulder_bottom, pin_z + self.leg_wide_half)),
					box_between((inner_x, -self.leg_reach, pin_z - self.leg_tip_half),
					            (outer_x, -self.shoulder_drop, pin_z + self.leg_tip_half)),
			):
				leg_part.draw(self.leg_rgb)

	def _draw_top_marks(self):
		label_length, label_width = self._label_size()
		top = self.body_height + 0.001
		half_length, half_width = label_length / 2, label_width / 2
		color((255, 255, 255))
		textured_quad(self._label_texture,
		              (-half_width, top, -half_length), (-half_width, top, half_length),
		              (half_width, top, half_length), (half_width, top, -half_length))
		mark_top = self.body_height + 0.002
		self._draw_half_disc(mark_top)
		self._draw_disc(mark_top, -self.body_half_width + 0.2, -self.body_half_length + 0.3)

	def _draw_half_disc(self, y):
		color(self.mark_rgb)
		glNormal3f(0.0, 1.0, 0.0)
		glBegin(GL_TRIANGLE_FAN)
		glVertex3f(0.0, y, -self.body_half_length)
		for index in range(17):
			angle = math.pi * index / 16
			glVertex3f(self.notch_radius * math.cos(angle), y, -self.body_half_length + self.notch_radius * math.sin(angle))
		glEnd()

	def _draw_disc(self, y, centre_x, centre_z):
		color(self.mark_rgb)
		glNormal3f(0.0, 1.0, 0.0)
		glBegin(GL_TRIANGLE_FAN)
		glVertex3f(centre_x, y, centre_z)
		for index in range(25):
			angle = 2.0 * math.pi * index / 24
			glVertex3f(centre_x + self.dot_radius * math.cos(angle), y, centre_z + self.dot_radius * math.sin(angle))
		glEnd()
