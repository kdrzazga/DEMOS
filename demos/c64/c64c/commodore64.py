"""3D model of a Commodore 64 (the later, flat "C64C" case).

Proportions come from the three reference photos in resources/: the case
profile from right-side.jpg, the key layout from top-front.png and the rear
connectors from c64c-back-side.jpg.

World frame (centimetres): x to the right, y up, z toward the user. The case is
centred on x and z and stands on y = 0.

The case is the side profile extruded across the width. The sloping face in
front of the vents carries the keyboard: everything on it is built in the
"keyboard frame" - x right, y along the slope's normal, z down the slope toward
the front edge - with the slope's front edge at the origin.
"""

import math
import os

from OpenGL.GL import *

import demos.c64.c64c.keys as k
from demos.c64.geometry import color, image_texture, quad, text_texture, textured_quad


class Commodore64:

	def __init__(self, width=40.4,
	             profile=((10.3, 0.0), (10.8, 0.8), (10.6, 1.25), (-3.4, 4.9), (-4.0, 5.6),
	                      (-4.6, 5.7), (-10.4, 5.4), (-10.8, 5.0), (-10.8, 0.0)),
	             key_pitch=1.85):
		self.width = width
		self.profile = profile
		self.slope_edge = 2
		self.vent_edge = 5
		self.side_cap_centre = (-3.0, 2.5)
		self.seam = ((-10.8, 2.4), (4.0, 2.4), (10.75, 0.85))
		self.vent_count = 10
		self.vent_side_margin = 1.6

		self.key_pitch = key_pitch
		self.cap_height = 1.15
		self.well_depth = 0.5
		self.well_margin = 0.15
		self.keyboard_left = -17.0
		self.keyboard_back_inset = 0.8
		self.function_column = 16.6
		self.space_column = 2.5

		self.case_color = (216, 206, 175)
		self.well_color = (92, 82, 66)
		self.vent_color = (140, 130, 106)
		self.seam_color = (130, 120, 98)
		self.port_black = (26, 24, 22)
		self.port_grey = (62, 60, 56)
		self.board_green = (40, 66, 44)
		self.contact_gold = (206, 170, 84)
		self.badge_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "plate.png")
		self.badge_left = 8.3
		self.badge_width = 10.0
		self.badge_front = -1.4
		self.label_ink = (140, 130, 108)
		self.led_color = (255, 40, 30)

		self.keyboard_rows = (
			(k.KeyArrowLeft(), k.Key1(), k.Key2(), k.Key3(), k.Key4(), k.Key5(), k.Key6(), k.Key7(),
			 k.Key8(), k.Key9(), k.Key0(), k.KeyPlus(), k.KeyMinus(), k.KeyPound(), k.KeyClrHome(),
			 k.KeyInstDel()),
			(k.KeyControl(), k.KeyQ(), k.KeyW(), k.KeyE(), k.KeyR(), k.KeyT(), k.KeyY(), k.KeyU(),
			 k.KeyI(), k.KeyO(), k.KeyP(), k.KeyAt(), k.KeyAsterisk(), k.KeyArrowUp(), k.KeyRestore()),
			(k.KeyRunStop(), k.KeyShiftLock(), k.KeyA(), k.KeyS(), k.KeyD(), k.KeyF(), k.KeyG(), k.KeyH(),
			 k.KeyJ(), k.KeyK(), k.KeyL(), k.KeyColon(), k.KeySemicolon(), k.KeyEquals(), k.KeyReturn()),
			(k.KeyCommodore(), k.KeyLeftShift(), k.KeyZ(), k.KeyX(), k.KeyC(), k.KeyV(), k.KeyB(), k.KeyN(),
			 k.KeyM(), k.KeyLessThan(), k.KeyGreaterThan(), k.KeyQuestionMark(), k.KeyRightShift(),
			 k.KeyCursorUpDown(), k.KeyCursorLeftRight()),
		)
		self.function_keys = (k.KeyF1(), k.KeyF3(), k.KeyF5(), k.KeyF7())
		self.space_bar = k.KeySpace()
		self.keys = tuple(key for row in self.keyboard_rows for key in row) + self.function_keys + (self.space_bar,)

		slope_front_z, slope_front_y = self.profile[self.slope_edge]
		slope_back_z, slope_back_y = self.profile[self.slope_edge + 1]
		self.slope_origin = (slope_front_z, slope_front_y)
		self.slope_length = math.hypot(slope_front_z - slope_back_z, slope_back_y - slope_front_y)
		self.slope_degrees = math.degrees(math.atan2(slope_back_y - slope_front_y, slope_front_z - slope_back_z))
		self.top_row_back = self.slope_length - self.keyboard_back_inset

		self._place_keys()
		self._display_list = None
		self._textures = []


	def _place_keys(self):
		for row_index, row in enumerate(self.keyboard_rows):
			column = 0.0
			for key in row:
				key.row, key.column = row_index, column
				column += key.width
		for row_index, key in enumerate(self.function_keys):
			key.row, key.column = row_index, self.function_column
		self.space_bar.row, self.space_bar.column = len(self.keyboard_rows), self.space_column

		self._key_positions = tuple((key, self._key_centre(key)) for key in self.keys)

	def _key_centre(self, key):
		x = self.keyboard_left + (key.column + key.width / 2) * self.key_pitch
		z = -(self.top_row_back - (key.row + 0.5) * self.key_pitch)
		return x, -self.well_depth, z

	def _keyboard_holes(self):
		"""Rectangles (x0, x1, z0, z1) cut into the slope, in the keyboard frame."""
		pitch, margin, left = self.key_pitch, self.well_margin, self.keyboard_left
		row_count = len(self.keyboard_rows)
		back_z = -self.top_row_back - margin
		rows_front_z = -(self.top_row_back - row_count * pitch)
		space_front_z = -(self.top_row_back - (row_count + 1) * pitch)
		main_width = sum(key.width for key in self.keyboard_rows[0])
		function_width = self.function_keys[0].width
		return (
			(left - margin, left + main_width * pitch + margin, back_z, rows_front_z + margin),
			(left + self.space_column * pitch - margin,
			 left + (self.space_column + self.space_bar.width) * pitch + margin,
			 rows_front_z, space_front_z + margin),
			(left + self.function_column * pitch - margin,
			 left + (self.function_column + function_width) * pitch + margin,
			 back_z, rows_front_z + margin),
		)


	def build(self):
		"""Create textures and display lists. Needs a GL context."""
		for key in self.keys:
			key.build(self.key_pitch, self.cap_height)

		self._badge_texture, self._badge_aspect = image_texture(self.badge_image)
		self._label_textures = {text: self._label_texture(text, aspect) for text, aspect in (
			("CONTROL PORT 1", 9.0), ("CONTROL PORT 2", 9.0), ("POWER", 5.0), ("ON", 1.6), ("OFF", 1.6))}
		self._textures = [self._badge_texture, *self._label_textures.values()]

		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_shell()
		glPushMatrix()
		self._enter_keyboard_frame()
		self._draw_keyboard_surface()
		self._draw_badge()
		self._draw_power_led()
		glPopMatrix()
		self._draw_vents()
		self._draw_seams()
		self._draw_back_panel()
		self._draw_right_panel()
		glEndList()

	def _label_texture(self, text, aspect):
		height_px = 64
		return text_texture(int(height_px * aspect), height_px, (0, 0, 0, 0),
		                    ((text, 44, self.label_ink, (0.5, 0.5)),))

	def _enter_keyboard_frame(self):
		slope_front_z, slope_front_y = self.slope_origin
		glTranslatef(0.0, slope_front_y, slope_front_z)
		glRotatef(self.slope_degrees, 1.0, 0.0, 0.0)

	def _draw_shell(self):
		half_width = self.width / 2
		color(self.case_color)
		glBegin(GL_QUADS)
		for index, (z0, y0) in enumerate(self.profile):
			if index == self.slope_edge:
				continue
			z1, y1 = self.profile[(index + 1) % len(self.profile)]
			quad((-half_width, y0, z0), (half_width, y0, z0), (half_width, y1, z1), (-half_width, y1, z1))
		glEnd()

		centre_z, centre_y = self.side_cap_centre
		outline = self.profile + self.profile[:1]
		for side in (-1.0, 1.0):
			x = side * half_width
			glBegin(GL_TRIANGLE_FAN)
			glNormal3f(side, 0.0, 0.0)
			glVertex3f(x, centre_y, centre_z)
			for z, y in (outline if side < 0 else reversed(outline)):
				glVertex3f(x, y, z)
			glEnd()

	def _draw_keyboard_surface(self):
		"""The slope face with the key wells cut out of it.

		The face is split into a grid along every hole edge; each cell is either
		solid slope or part of a well (plate at the bottom, walls toward solid
		neighbours), which handles holes that touch or overlap.
		"""
		holes = self._keyboard_holes()
		half_width = self.width / 2
		xs = sorted({-half_width, half_width, *(edge for hole in holes for edge in hole[:2])})
		zs = sorted({-self.slope_length, 0.0, *(edge for hole in holes for edge in hole[2:])})

		def is_well(i, j):
			centre_x, centre_z = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
			return any(x0 < centre_x < x1 and z0 < centre_z < z1 for x0, x1, z0, z1 in holes)

		cells = [(i, j) for i in range(len(xs) - 1) for j in range(len(zs) - 1)]
		floor = -self.well_depth

		color(self.case_color)
		glBegin(GL_QUADS)
		for i, j in cells:
			if not is_well(i, j):
				quad((xs[i], 0.0, zs[j + 1]), (xs[i + 1], 0.0, zs[j + 1]), (xs[i + 1], 0.0, zs[j]), (xs[i], 0.0, zs[j]))
		glEnd()

		color(self.well_color)
		glBegin(GL_QUADS)
		for i, j in cells:
			if is_well(i, j):
				quad((xs[i], floor, zs[j + 1]), (xs[i + 1], floor, zs[j + 1]), (xs[i + 1], floor, zs[j]), (xs[i], floor, zs[j]))
		glEnd()

		color(self.case_color, 0.8)
		glBegin(GL_QUADS)
		for i, j in cells:
			if not is_well(i, j):
				continue
			x0, x1, z0, z1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
			if not is_well(i - 1, j):
				quad((x0, 0.0, z0), (x0, 0.0, z1), (x0, floor, z1), (x0, floor, z0))
			if not is_well(i + 1, j):
				quad((x1, 0.0, z1), (x1, 0.0, z0), (x1, floor, z0), (x1, floor, z1))
			if not is_well(i, j - 1):
				quad((x1, 0.0, z0), (x0, 0.0, z0), (x0, floor, z0), (x1, floor, z0))
			if not is_well(i, j + 1):
				quad((x0, 0.0, z1), (x1, 0.0, z1), (x1, floor, z1), (x0, floor, z1))
		glEnd()

	def _draw_badge(self):
		x0, x1 = self.badge_left, self.badge_left + self.badge_width
		front_z, lift = self.badge_front, 0.01
		back_z = front_z - self.badge_width / self._badge_aspect
		glColor3f(1.0, 1.0, 1.0)
		textured_quad(self._badge_texture, (x0, lift, front_z), (x1, lift, front_z), (x1, lift, back_z), (x0, lift, back_z))

	def _draw_power_led(self):
		x0, x1 = self.keyboard_left + 0.1, self.keyboard_left + 0.8
		z0, z1, lift = -(self.slope_length - 0.25), -(self.slope_length - 0.45), 0.01
		glDisable(GL_LIGHTING)
		color(self.led_color)
		glBegin(GL_QUADS)
		for x, z in ((x0, z1), (x1, z1), (x1, z0), (x0, z0)):
			glVertex3f(x, lift, z)
		glEnd()
		glEnable(GL_LIGHTING)

	def _draw_vents(self):
		(start_z, start_y), (end_z, end_y) = self.profile[self.vent_edge], self.profile[self.vent_edge + 1]
		edge_z, edge_y = end_z - start_z, end_y - start_y
		length = math.hypot(edge_z, edge_y)
		normal_z, normal_y = edge_y / length * 0.01, -edge_z / length * 0.01
		half_span = self.width / 2 - self.vent_side_margin

		def point_along(t, x):
			return x, start_y + edge_y * t + normal_y, start_z + edge_z * t + normal_z

		color(self.vent_color)
		glBegin(GL_QUADS)
		for index in range(self.vent_count):
			t0 = 0.06 + index * 0.092
			t1 = t0 + 0.045
			quad(point_along(t0, -half_span), point_along(t0, half_span), point_along(t1, half_span), point_along(t1, -half_span))
		glEnd()

	def _draw_seams(self):
		half_width = self.width / 2 + 0.01
		back_z = self.profile[-1][0] - 0.01
		seam_y = self.seam[0][1]
		glDisable(GL_LIGHTING)
		glLineWidth(1.5)
		color(self.seam_color)
		for x in (-half_width, half_width):
			glBegin(GL_LINE_STRIP)
			for z, y in self.seam:
				glVertex3f(x, y, z)
			glEnd()
		glBegin(GL_LINES)
		glVertex3f(-half_width, seam_y, back_z)
		glVertex3f(half_width, seam_y, back_z)
		glEnd()
		glEnable(GL_LIGHTING)


	def _draw_back_panel(self):
		glPushMatrix()
		glTranslatef(0.0, 0.0, self.profile[-1][0])
		glRotatef(180.0, 0.0, 1.0, 0.0)
		self._edge_connector(-15.7, -8.6, 0.0, 2.2, contacts=22)
		self._panel_rect(-7.0, 1.36, -6.4, 1.8, (90, 120, 160), 1)
		self._panel_disc(-3.87, 1.67, 0.45, (190, 185, 170), 1)
		self._panel_disc(-3.87, 1.67, 0.22, self.port_black, 2)
		self._panel_disc(-3.87, 1.67, 0.06, (190, 185, 170), 3)
		self._din_socket(-0.15, 1.5, 0.85, pins=8)
		self._din_socket(2.75, 1.5, 0.85, pins=6)
		self._edge_connector(4.65, 9.6, 0.0, 1.36, contacts=6)
		self._edge_connector(10.5, 17.9, 0.0, 1.36, contacts=12)
		glPopMatrix()

	def _draw_right_panel(self):
		glPushMatrix()
		glTranslatef(self.width / 2, 0.0, 0.0)
		glRotatef(90.0, 0.0, 1.0, 0.0)
		self._panel_rect(0.4, 0.3, 9.6, 2.2, tuple(channel * 0.93 for channel in self.case_color), 0.5)
		self._joystick_port(0.6, 2.8, 0.85, 1.7)
		self._joystick_port(3.6, 5.8, 0.85, 1.7)
		self._panel_rect(6.6, 0.85, 7.2, 1.65, self.port_black, 1)
		self._panel_rect(6.65, 1.25, 7.15, 1.6, self.port_grey, 2)
		self._panel_rect(7.5, 0.75, 8.95, 2.0, self.port_black, 1)
		self._din_socket(8.22, 1.37, 0.5, pins=7)
		self._panel_label("CONTROL PORT 1", 0.3, 0.38, 3.1, 0.68)
		self._panel_label("CONTROL PORT 2", 3.3, 0.38, 6.1, 0.68)
		self._panel_label("POWER", 7.45, 0.38, 9.0, 0.68)
		self._panel_label("ON", 6.05, 1.35, 6.55, 1.65)
		self._panel_label("OFF", 6.05, 0.85, 6.55, 1.15)
		glPopMatrix()

	def _panel_rect(self, a0, b0, a1, b1, rgb, layer):
		self._panel_polygon(((a0, b0), (a1, b0), (a1, b1), (a0, b1)), rgb, layer)

	def _panel_polygon(self, points, rgb, layer):
		color(rgb)
		glBegin(GL_POLYGON)
		glNormal3f(0.0, 0.0, 1.0)
		for a, b in points:
			glVertex3f(a, b, layer * 0.01)
		glEnd()

	def _panel_disc(self, centre_a, centre_b, radius, rgb, layer, segments=32):
		color(rgb)
		glBegin(GL_TRIANGLE_FAN)
		glNormal3f(0.0, 0.0, 1.0)
		glVertex3f(centre_a, centre_b, layer * 0.01)
		for step in range(segments + 1):
			angle = 2 * math.pi * step / segments
			glVertex3f(centre_a + radius * math.cos(angle), centre_b + radius * math.sin(angle), layer * 0.01)
		glEnd()

	def _panel_label(self, text, a0, b0, a1, b1):
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor3f(1.0, 1.0, 1.0)
		layer = 0.01
		textured_quad(self._label_textures[text], (a0, b0, layer), (a1, b0, layer), (a1, b1, layer), (a0, b1, layer))
		glDisable(GL_BLEND)

	def _edge_connector(self, a0, a1, b0, b1, contacts):
		"""Slot in the case with the edge of the main board showing inside."""
		self._panel_rect(a0, b0, a1, b1, self.port_black, 1)
		board_bottom, board_top = (b0 + b1) / 2 - 0.14, (b0 + b1) / 2 + 0.14
		board_left, board_right = a0 + 0.25, a1 - 0.25
		self._panel_rect(board_left, board_bottom, board_right, board_top, self.board_green, 2)
		spacing = (board_right - board_left) / contacts
		for index in range(contacts):
			left = board_left + index * spacing + spacing * 0.2
			self._panel_rect(left, board_bottom + 0.03, left + spacing * 0.6, board_top - 0.03, self.contact_gold, 3)

	def _din_socket(self, centre_a, centre_b, radius, pins):
		self._panel_disc(centre_a, centre_b, radius, self.port_black, 1)
		self._panel_disc(centre_a, centre_b, radius * 0.78, self.port_grey, 2)
		pin_radius, pin_circle = radius * 0.08, radius * 0.48
		ring_pins = pins - 1
		for index in range(ring_pins):
			angle = math.radians(200 - index * 220 / (ring_pins - 1))
			self._panel_disc(centre_a + pin_circle * math.cos(angle), centre_b + pin_circle * math.sin(angle),
			                 pin_radius, self.port_black, 3, segments=10)
		self._panel_disc(centre_a, centre_b, pin_radius, self.port_black, 3, segments=10)
		self._panel_rect(centre_a - radius * 0.12, centre_b - radius * 0.8, centre_a + radius * 0.12,
		                 centre_b - radius * 0.62, self.port_black, 3)

	def _joystick_port(self, a0, a1, b0, b1):
		"""Male DE-9: a D-shaped shell, wider at the top, with 5 + 4 pins."""
		taper = 0.22
		self._panel_polygon(((a0 + taper, b0), (a1 - taper, b0), (a1, b1), (a0, b1)), self.port_black, 1)
		inset = 0.14
		self._panel_polygon(((a0 + taper + inset, b0 + inset), (a1 - taper - inset, b0 + inset),
		                     (a1 - inset, b1 - inset), (a0 + inset, b1 - inset)), self.port_grey, 2)
		centre_a = (a0 + a1) / 2
		pin_pitch = (a1 - a0 - 2 * inset) / 5.6
		for pin_count, row_b in ((5, b0 + (b1 - b0) * 0.64), (4, b0 + (b1 - b0) * 0.36)):
			for index in range(pin_count):
				pin_a = centre_a + (index - (pin_count - 1) / 2) * pin_pitch
				self._panel_disc(pin_a, row_b, 0.06, self.contact_gold, 3, segments=10)


	def press(self, pygame_key, is_down):
		for key in self.keys:
			if key.handles(pygame_key):
				key.on_pc_key(is_down)

	def update(self):
		for key in self.keys:
			key.update()

	def key_world_positions(self):
		"""(key, (x, y, z)) for every key's footprint centre in world coordinates."""
		slope_front_z, slope_front_y = self.slope_origin
		slope = math.radians(self.slope_degrees)
		return tuple((key, (x,
		                    slope_front_y + y * math.cos(slope) - z * math.sin(slope),
		                    slope_front_z + y * math.sin(slope) + z * math.cos(slope)))
		             for key, (x, y, z) in self._key_positions)

	def draw_case(self):
		glCallList(self._display_list)

	def draw(self):
		self.draw_case()
		glPushMatrix()
		self._enter_keyboard_frame()
		for key, (x, y, z) in self._key_positions:
			glPushMatrix()
			glTranslatef(x, y, z)
			key.draw()
			glPopMatrix()
		glPopMatrix()

	def destroy(self):
		for key in self.keys:
			key.destroy()
		if self._display_list:
			glDeleteLists(self._display_list, 1)
		if self._textures:
			glDeleteTextures(self._textures)
