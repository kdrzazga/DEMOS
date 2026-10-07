"""Separate components of the Commodore Datasette (C2N / 1530) model.

Each part builds its own display lists and draws itself in its own local frame;
``Datasette`` (datasette.py) places them on the case. All lengths are in
centimetres; every local frame has x to the right, y up and z toward the front
of the recorder, like the world frame of the C64 model.

* ``DatasetteButton`` and its six subclasses - the dark-brown piano keys.
* ``CassetteDoor`` - the hinged lid with its smoked window, plus the compartment
  under it (tape spindles visible through the window).
* ``TapeCounter`` - the three-digit rolling counter with its black reset button.
* ``DatasetteCable`` - the grey lead (common ``Cable``) ending in the edge-connector plug.
"""

import math

import pygame
from OpenGL.GL import *

from demos.c64.cable import Cable
from demos.c64.geometry import color, face_normal, quad, upload_texture

BUTTON_BROWN = (72, 54, 44)
LABEL_INK = (70, 64, 56)


def box(x0, x1, y0, y1, z0, z1, skip_bottom=True):
	"""Axis-aligned box; call between glBegin(GL_QUADS) / glEnd()."""
	quad((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0))
	quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
	quad((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0))
	quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))
	quad((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))
	if not skip_bottom:
		quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))


def disc(centre_x, y, centre_z, radius, segments=24):
	"""Flat disc facing up."""
	rim = tuple((centre_x + radius * math.cos(angle), y, centre_z + radius * math.sin(angle))
	            for angle in (-2 * math.pi * step / segments for step in range(segments + 1)))
	glBegin(GL_TRIANGLE_FAN)
	glNormal3f(*face_normal((centre_x, y, centre_z), rim[0], rim[1]))
	glVertex3f(centre_x, y, centre_z)
	for corner in rim:
		glVertex3f(*corner)
	glEnd()


def cylinder(centre_x, y0, y1, centre_z, radius, segments=24):
	"""Upright open cylinder wall."""
	glBegin(GL_QUADS)
	for step in range(segments):
		a0, a1 = 2 * math.pi * step / segments, 2 * math.pi * (step + 1) / segments
		p0 = (centre_x + radius * math.cos(a0), centre_z + radius * math.sin(a0))
		p1 = (centre_x + radius * math.cos(a1), centre_z + radius * math.sin(a1))
		quad((p0[0], y0, p0[1]), (p0[0], y1, p0[1]), (p1[0], y1, p1[1]), (p1[0], y0, p1[1]))
	glEnd()


class DatasetteButton:
	"""One piano key. Local frame: origin at the key's back-bottom centre (on the
	button bay floor, against the bay's back wall), z toward the front.

	The side profile is extruded across the key's width; the top slopes a little
	down toward the front and the front edge is bevelled."""

	def __init__(self, label, symbol, pygame_keys=(), latching=True, button_color=BUTTON_BROWN):
		self.label = label
		self.symbol = symbol
		self.pygame_keys = pygame_keys
		self.latching = latching
		self.button_color = button_color
		self.width = 1.48
		self.depth = 2.95
		self.back_height = 2.065
		self.front_height = 1.47
		self.bevel = 0.25
		self.press_depth = 0.35
		self.press_rate = 0.45
		self.release_rate = 0.25

		self.held = False
		self.latched = False
		self.travel = 0.0
		self._display_list = None

	def handles(self, pygame_key):
		return pygame_key in self.pygame_keys

	def profile(self):
		"""Side outline as (z, y) points, counter-clockwise seen from the right."""
		return ((0.0, 0.0), (self.depth, 0.0), (self.depth, self.front_height),
		        (self.depth - self.bevel, self.front_height + self.bevel), (0.0, self.back_height))

	def build(self):
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_key()
		glEndList()

	def _draw_key(self):
		half_width = self.width / 2
		outline = self.profile()
		color(self.button_color)
		glBegin(GL_QUADS)
		for index, (z0, y0) in enumerate(outline):
			z1, y1 = outline[(index + 1) % len(outline)]
			if y0 == 0.0 and y1 == 0.0:
				continue
			quad((-half_width, y0, z0), (-half_width, y1, z1), (half_width, y1, z1), (half_width, y0, z0))
		glEnd()
		color(self.button_color, 0.85)
		for x, points in ((half_width, outline), (-half_width, tuple(reversed(outline)))):
			corners = tuple((x, y, z) for z, y in points)
			glBegin(GL_POLYGON)
			glNormal3f(*face_normal(*corners[:3]))
			for corner in corners:
				glVertex3f(*corner)
			glEnd()

	def paint_label(self, surface, centre_x_px, centre_y_px, font, ink):
		"""Print the label and its transport symbol onto the case-label texture."""
		text = font.render(self.label, True, ink)
		symbol_size = font.get_height() * 0.5
		gap = symbol_size * 0.4
		total_width = text.get_width() + gap + symbol_size * self._symbol_width_factor()
		left = centre_x_px - total_width / 2
		surface.blit(text, text.get_rect(midleft=(left, centre_y_px)))
		self._paint_symbol(surface, left + text.get_width() + gap, centre_y_px, symbol_size, ink)

	def _symbol_width_factor(self):
		return 2.0 if self.symbol in ("rewind", "fast_forward") else 1.0

	def _paint_symbol(self, surface, left, centre_y, size, ink):
		half = size / 2
		top, bottom = centre_y - half, centre_y + half
		if self.symbol == "dot":
			pygame.draw.circle(surface, ink, (left + half, centre_y), half)
		elif self.symbol == "play":
			pygame.draw.polygon(surface, ink, ((left, top), (left + size, centre_y), (left, bottom)))
		elif self.symbol == "fast_forward":
			for offset in (0.0, size):
				pygame.draw.polygon(surface, ink, ((left + offset, top), (left + offset + size, centre_y), (left + offset, bottom)))
		elif self.symbol == "rewind":
			for offset in (0.0, size):
				pygame.draw.polygon(surface, ink, ((left + offset + size, top), (left + offset, centre_y), (left + offset + size, bottom)))
		elif self.symbol == "stop":
			pygame.draw.rect(surface, ink, pygame.Rect(left, top, size, size))
		elif self.symbol == "eject":
			pygame.draw.polygon(surface, ink, ((left, centre_y + half * 0.3), (left + half, top), (left + size, centre_y + half * 0.3)))
			pygame.draw.rect(surface, ink, pygame.Rect(left, centre_y + half * 0.55, size, half * 0.45))

	def update(self):
		down = self.held or self.latched
		target = self.press_depth if down else 0.0
		rate = self.press_rate if down else self.release_rate
		self.travel += (target - self.travel) * rate
		if abs(self.travel - target) < 0.001:
			self.travel = target

	def draw(self):
		glPushMatrix()
		glTranslatef(0.0, -self.travel, 0.0)
		glCallList(self._display_list)
		glPopMatrix()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)


class ButtonRecord(DatasetteButton):
	def __init__(self):
		super().__init__("RECORD", "dot", pygame_keys=(pygame.K_1, pygame.K_F1))


class ButtonPlay(DatasetteButton):
	def __init__(self):
		super().__init__("PLAY", "play", pygame_keys=(pygame.K_2, pygame.K_F2))


class ButtonRewind(DatasetteButton):
	def __init__(self):
		super().__init__("REWIND", "rewind", pygame_keys=(pygame.K_3, pygame.K_F3))


class ButtonFastForward(DatasetteButton):
	def __init__(self):
		super().__init__("F.FWD", "fast_forward", pygame_keys=(pygame.K_4, pygame.K_F4))


class ButtonStop(DatasetteButton):
	def __init__(self):
		super().__init__("STOP", "stop", pygame_keys=(pygame.K_5, pygame.K_F5), latching=False)


class ButtonEject(DatasetteButton):
	def __init__(self):
		super().__init__("EJECT", "eject", pygame_keys=(pygame.K_6, pygame.K_F6), latching=False)


class CassetteDoor:
	"""The cassette lid and the compartment under it.

	Local frame: origin at the middle of the hinge, which runs along x at the
	back edge of the lid, level with the top of the case. The lid covers
	x in [-width/2, width/2] and z in [0, depth]; the compartment goes down
	from y = 0. The lid swings up around the hinge when open."""

	def __init__(self, width=9.8, depth=7.2, compartment_depth=1.54):
		self.width = width
		self.depth = depth
		self.compartment_depth = compartment_depth
		self.lid_thickness = 0.22
		self.frame_side = 0.85
		self.frame_back = 0.75
		self.frame_front = 1.35
		self.frame_color = (178, 180, 184)
		self.frame_edge_color = (128, 130, 134)
		self.window_color = (34, 32, 34)
		self.window_alpha = 0.62
		self.compartment_color = (46, 44, 42)
		self.mechanism_color = (70, 70, 72)
		self.hub_color = (22, 22, 22)
		self.hub_teeth_color = (200, 200, 196)
		self.auto_stop_color = (220, 120, 40)
		self.hub_radius = 0.42
		self.hub_spacing = 4.3
		self.hub_height = 0.63
		self.open_degrees = 38.0
		self.swing_rate = 0.12

		self.is_open = False
		self.angle = 0.0
		self.hub_turns = 0.0
		self._display_list = None

	def toggle(self):
		self.is_open = not self.is_open

	def build(self):
		self._display_list = glGenLists(2)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_compartment()
		glEndList()
		glNewList(self._display_list + 1, GL_COMPILE)
		self._draw_lid_frame()
		glEndList()

	def _draw_compartment(self):
		half_width, floor = self.width / 2 - 0.1, -self.compartment_depth
		front, back = self.depth - 0.1, 0.1
		color(self.compartment_color)
		glBegin(GL_QUADS)
		quad((-half_width, floor, front), (half_width, floor, front), (half_width, floor, back), (-half_width, floor, back))
		quad((-half_width, 0.0, back), (half_width, 0.0, back), (half_width, floor, back), (-half_width, floor, back))
		quad((half_width, 0.0, front), (-half_width, 0.0, front), (-half_width, floor, front), (half_width, floor, front))
		quad((-half_width, 0.0, front), (-half_width, 0.0, back), (-half_width, floor, back), (-half_width, floor, front))
		quad((half_width, 0.0, back), (half_width, 0.0, front), (half_width, floor, front), (half_width, floor, back))
		glEnd()

		mechanism_top = floor + 0.35
		color(self.mechanism_color)
		glBegin(GL_QUADS)
		box(-half_width + 0.6, half_width - 0.6, floor, mechanism_top, back + 0.8, front - 1.6)
		glEnd()
		color(self.auto_stop_color)
		glBegin(GL_QUADS)
		box(-0.6, 0.6, mechanism_top, mechanism_top + 0.08, front - 2.5, front - 1.9)
		glEnd()

	def hub_centres(self):
		"""Spindle centres (x, z) in the door's frame."""
		centre_z = self.depth * 0.45
		return ((-self.hub_spacing / 2, centre_z), (self.hub_spacing / 2, centre_z))

	def _draw_hubs(self):
		floor = -self.compartment_depth
		top = floor + self.hub_height
		for index, (centre_x, centre_z) in enumerate(self.hub_centres()):
			color(self.hub_color)
			cylinder(centre_x, floor, top, centre_z, self.hub_radius)
			disc(centre_x, top, centre_z, self.hub_radius)
			direction = 1.0 if index else -1.0
			spin = direction * self.hub_turns * 2 * math.pi
			color(self.hub_teeth_color)
			glBegin(GL_QUADS)
			for tooth in range(6):
				angle = spin + tooth * math.pi / 3
				radial_x, radial_z = math.cos(angle), math.sin(angle)
				side_x, side_z = -radial_z * 0.06, radial_x * 0.06
				inner, outer = self.hub_radius * 0.35, self.hub_radius * 0.9
				lift = top + 0.01
				quad((centre_x + radial_x * inner - side_x, lift, centre_z + radial_z * inner - side_z),
				     (centre_x + radial_x * inner + side_x, lift, centre_z + radial_z * inner + side_z),
				     (centre_x + radial_x * outer + side_x, lift, centre_z + radial_z * outer + side_z),
				     (centre_x + radial_x * outer - side_x, lift, centre_z + radial_z * outer - side_z))
			glEnd()

	def _window_rect(self):
		half_width = self.width / 2
		return -half_width + self.frame_side, half_width - self.frame_side, self.frame_back, self.depth - self.frame_front

	def _draw_lid_frame(self):
		half_width, top, bottom = self.width / 2, self.lid_thickness, 0.0
		window_left, window_right, window_back, window_front = self._window_rect()
		color(self.frame_color)
		glBegin(GL_QUADS)
		for x0, x1, z0, z1 in ((-half_width, half_width, 0.0, window_back),
		                       (-half_width, half_width, window_front, self.depth),
		                       (-half_width, window_left, window_back, window_front),
		                       (window_right, half_width, window_back, window_front)):
			quad((x0, top, z1), (x1, top, z1), (x1, top, z0), (x0, top, z0))
			quad((x0, bottom, z0), (x1, bottom, z0), (x1, bottom, z1), (x0, bottom, z1))
		glEnd()
		color(self.frame_edge_color)
		glBegin(GL_QUADS)
		quad((-half_width, bottom, self.depth), (half_width, bottom, self.depth), (half_width, top, self.depth), (-half_width, top, self.depth))
		quad((half_width, bottom, 0.0), (-half_width, bottom, 0.0), (-half_width, top, 0.0), (half_width, top, 0.0))
		quad((-half_width, bottom, 0.0), (-half_width, bottom, self.depth), (-half_width, top, self.depth), (-half_width, top, 0.0))
		quad((half_width, bottom, self.depth), (half_width, bottom, 0.0), (half_width, top, 0.0), (half_width, top, self.depth))
		inset = 0.12
		quad((window_left, top, window_back), (window_right, top, window_back), (window_right, top - inset, window_back), (window_left, top - inset, window_back))
		quad((window_right, top, window_front), (window_left, top, window_front), (window_left, top - inset, window_front), (window_right, top - inset, window_front))
		quad((window_left, top, window_front), (window_left, top, window_back), (window_left, top - inset, window_back), (window_left, top - inset, window_front))
		quad((window_right, top, window_back), (window_right, top, window_front), (window_right, top - inset, window_front), (window_right, top - inset, window_back))
		glEnd()
		grip_z = self.depth - self.frame_front * 0.5
		glBegin(GL_QUADS)
		for offset in (-0.18, 0.0, 0.18):
			quad((-1.2, top + 0.005, grip_z + offset + 0.04), (1.2, top + 0.005, grip_z + offset + 0.04),
			     (1.2, top + 0.005, grip_z + offset - 0.04), (-1.2, top + 0.005, grip_z + offset - 0.04))
		glEnd()

	def _draw_window(self):
		window_left, window_right, window_back, window_front = self._window_rect()
		height = self.lid_thickness - 0.12
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glDepthMask(GL_FALSE)
		glColor4f(self.window_color[0] / 255.0, self.window_color[1] / 255.0, self.window_color[2] / 255.0, self.window_alpha)
		glBegin(GL_QUADS)
		quad((window_left, height, window_front), (window_right, height, window_front),
		     (window_right, height, window_back), (window_left, height, window_back))
		glEnd()
		glDepthMask(GL_TRUE)
		glDisable(GL_BLEND)

	def update(self, hub_turns_delta=0.0):
		target = self.open_degrees if self.is_open else 0.0
		self.angle += (target - self.angle) * self.swing_rate
		if abs(self.angle - target) < 0.05:
			self.angle = target
		self.hub_turns += hub_turns_delta

	def draw_compartment(self):
		glCallList(self._display_list)
		self._draw_hubs()

	def draw_lid(self):
		glPushMatrix()
		glRotatef(-self.angle, 1.0, 0.0, 0.0)
		glCallList(self._display_list + 1)
		self._draw_window()
		glPopMatrix()

	def draw(self):
		self.draw_compartment()
		self.draw_lid()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 2)


class TapeCounter:
	"""Three-digit mechanical counter with its black reset button on the right.

	Local frame: origin at the centre of the counter housing's footprint on the
	case top. The digits read from the front; each wheel is a strip texture
	with 0..9,0 painted top to bottom, scrolled like an odometer."""

	def __init__(self, reset_keys=(pygame.K_r, pygame.K_0)):
		self.reset_keys = reset_keys
		self.housing_width = 2.2
		self.housing_depth = 1.3
		self.housing_height = 0.18
		self.digit_width = 0.5
		self.digit_height = 0.78
		self.digit_gap = 0.12
		self.housing_color = (24, 24, 24)
		self.digit_ink = (236, 236, 230)
		self.digit_paper = (18, 18, 18)
		self.reset_offset_x = 1.75
		self.reset_width = 0.55
		self.reset_depth = 0.75
		self.reset_height = 0.4
		self.reset_press_depth = 0.25
		self.reset_rate = 0.4
		self.digit_cell_px = 64

		self.value = 0.0
		self.reset_held = False
		self.reset_travel = 0.0
		self._display_list = None
		self._digit_texture = None

	def handles(self, pygame_key):
		return pygame_key in self.reset_keys

	def press_reset(self, is_down):
		self.reset_held = is_down
		if is_down:
			self.value = 0.0

	def advance(self, counts):
		self.value = (self.value + counts) % 1000.0

	def build(self):
		self._digit_texture = self._make_digit_strip()
		self._display_list = glGenLists(2)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_housing()
		glEndList()
		glNewList(self._display_list + 1, GL_COMPILE)
		self._draw_reset_button()
		glEndList()

	def _make_digit_strip(self):
		cell = self.digit_cell_px
		surface = pygame.Surface((cell, cell * 11), pygame.SRCALPHA)
		surface.fill(self.digit_paper)
		font = pygame.font.SysFont("arial", int(cell * 0.85), bold=True)
		for index in range(11):
			image = font.render(str(index % 10), True, self.digit_ink)
			surface.blit(image, image.get_rect(center=(cell // 2, cell * index + cell // 2)))
		return upload_texture(surface)

	def _draw_housing(self):
		half_width, half_depth = self.housing_width / 2, self.housing_depth / 2
		color(self.housing_color)
		glBegin(GL_QUADS)
		box(-half_width, half_width, 0.0, self.housing_height, -half_depth, half_depth)
		glEnd()

	def _draw_reset_button(self):
		half_width, half_depth = self.reset_width / 2, self.reset_depth / 2
		color(self.housing_color)
		glBegin(GL_QUADS)
		box(-half_width, half_width, -0.3, self.reset_height, -half_depth, half_depth)
		glEnd()

	def wheel_positions(self):
		"""Continuous position of each wheel (hundreds, tens, ones); the higher
		wheels only turn while the one to their right rolls from 9 to 0."""
		ones = self.value % 10.0
		tens = math.floor(self.value / 10.0) % 10 + max(0.0, self.value % 10.0 - 9.0)
		hundreds = math.floor(self.value / 100.0) % 10 + max(0.0, self.value % 100.0 - 99.0)
		return hundreds, tens, ones

	def _draw_digits(self):
		lift = self.housing_height + 0.005
		half_height = self.digit_height / 2
		pitch = self.digit_width + self.digit_gap
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._digit_texture)
		glColor3f(1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for index, position in enumerate(self.wheel_positions()):
			left = (index - 1) * pitch - self.digit_width / 2
			right = left + self.digit_width
			top_t = 1.0 - position / 11.0
			bottom_t = top_t - 1.0 / 11.0
			glTexCoord2f(0.0, bottom_t)
			glVertex3f(left, lift, half_height)
			glTexCoord2f(1.0, bottom_t)
			glVertex3f(right, lift, half_height)
			glTexCoord2f(1.0, top_t)
			glVertex3f(right, lift, -half_height)
			glTexCoord2f(0.0, top_t)
			glVertex3f(left, lift, -half_height)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def update(self):
		target = self.reset_press_depth if self.reset_held else 0.0
		self.reset_travel += (target - self.reset_travel) * self.reset_rate
		if abs(self.reset_travel - target) < 0.001:
			self.reset_travel = target

	def draw(self):
		glCallList(self._display_list)
		self._draw_digits()
		glPushMatrix()
		glTranslatef(self.reset_offset_x, -self.reset_travel, 0.0)
		glCallList(self._display_list + 1)
		glPopMatrix()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 2)
		if self._digit_texture:
			glDeleteTextures([self._digit_texture])


class DatasetteCable(Cable):
	"""Grey lead ending in the edge-connector plug that goes into the C64's
	cassette port."""

	def __init__(self, path, radius=0.26):
		super().__init__(path, radius, cable_color=(138, 140, 142), grommet_color=(96, 98, 100),
		                 grommet_radius=0.42, grommet_length=0.9)
		self.plug_color = (150, 152, 154)
		self.plug_rib_color = (112, 114, 116)
		self.slot_color = (20, 20, 20)
		self.plug_length = 2.6
		self.plug_width = 4.4
		self.plug_height = 1.1

	def slot_centre(self):
		"""Middle of the dark slot on the plug's front face."""
		return self.plug_point(self.plug_length + 0.005, 0.0, self.plug_height * 0.5)

	def _draw_plug(self, entry, forward):
		point = self._plug_frame(entry, forward)
		half_width, length, height = self.plug_width / 2, self.plug_length, self.plug_height
		corners = {(a, c, h): point(a * length, (c * 2 - 1) * half_width, h * height)
		           for a in (0, 1) for c in (0, 1) for h in (0, 1)}
		color(self.plug_color)
		glBegin(GL_QUADS)
		for face in (((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
		             ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
		             ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)),
		             ((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)),
		             ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1))):
			quad(*(corners[key] for key in face))
		glEnd()

		color(self.plug_rib_color)
		glBegin(GL_QUADS)
		for rib in range(5):
			along = length * (0.2 + rib * 0.13)
			for across in (-half_width - 0.005, half_width + 0.005):
				quad(point(along, across, height * 0.15), point(along + 0.06, across, height * 0.15),
				     point(along + 0.06, across, height * 0.85), point(along, across, height * 0.85))
		glEnd()

		front = length + 0.005
		color(self.slot_color)
		glBegin(GL_QUADS)
		quad(point(front, -half_width * 0.82, height * 0.38), point(front, half_width * 0.82, height * 0.38),
		     point(front, half_width * 0.82, height * 0.62), point(front, -half_width * 0.82, height * 0.62))
		glEnd()
