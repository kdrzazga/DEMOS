"""Separate components of the joystick model (a QuickShot II style stick).

Each part builds its own display lists and draws itself in its own local frame;
``Joystick`` (joystick.py) places them. Lengths are in centimetres; every
local frame has x to the right, y up and z toward the user.

* ``JoystickBase`` - the black box on four suction cups, with the raised
  platform, the rubber boot around the stick, logo and autofire switch.
* ``JoystickStick`` - the pistol grip with its finger grooves and neck.
* ``FireButton`` with ``TriggerButton`` and ``TopButton`` - the two red buttons.
* ``JoystickCable`` - the black lead ending in the 9-pin D-sub socket.
"""

import math

import pygame
from OpenGL.GL import *

from demos.c64.cable import Cable
from demos.c64.geometry import color, face_normal, quad, textured_quad, upload_texture
from demos.c64.surfaces import (circle_outline, draw_cap, draw_ring_surface, ring, rounded_rect_outline,
                                superellipse_outline)

JOYSTICK_BLACK = (36, 36, 38)
BOOT_BLACK = (22, 22, 22)
FIRE_RED = (212, 32, 30)


class JoystickBase:
	"""Local frame: origin at the middle of the floor under the base."""

	def __init__(self, width=10.0, depth=10.6, corner_radius=1.6,
	             rings=((0.55, 0.35), (0.7, 0.1), (0.85, 0.0), (3.0, 0.0), (3.25, 0.15), (3.45, 0.45),
	                    (3.5, 0.7))):
		self.width = width
		self.depth = depth
		self.corner_radius = corner_radius
		self.rings = rings
		self.top_y = rings[-1][0]
		self.body_color = JOYSTICK_BLACK
		self.groove_color = (14, 14, 14)
		self.groove_height = 1.75

		self.platform_centre_z = -0.3
		self.platform_half_size = 2.8
		self.platform_radius = 0.9
		self.platform_rings = ((0.0, 0.0), (0.35, 0.0), (0.5, 0.2))
		self.platform_color = (42, 42, 44)

		self.boot_rings = ((0.0, 2.0, 0.6), (0.25, 1.75, 0.55), (0.6, 1.35, 0.45), (1.0, 1.0, 0.35))
		self.boot_color = BOOT_BLACK
		self.pivot_depth_in_boot = 0.4

		self.foot_inset = 1.4
		self.foot_top_radius = 0.85
		self.foot_bottom_radius = 1.25
		self.foot_color = (26, 26, 26)

		self.logo_rect = (-3.4, 3.4, 2.95, 4.15)
		self.logo_white = (236, 236, 236)
		self.logo_red = FIRE_RED

		self.switch_rect = (-1.2, 0.4, 1.7, 2.5)
		self.switch_color = (60, 60, 62)

		self._display_list = None
		self._logo_texture = None

	def platform_top(self):
		return self.top_y + self.platform_rings[-1][0]

	def stick_pivot(self):
		"""Where the stick's pivot sits: inside the boot, over the platform centre."""
		boot_top = self.platform_top() + self.boot_rings[-1][0]
		return 0.0, boot_top - self.pivot_depth_in_boot, self.platform_centre_z

	def cable_exit(self):
		return 2.0, 1.6, -self.depth / 2

	def build(self):
		self._logo_texture = self._make_logo_texture()
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_body()
		self._draw_groove()
		self._draw_platform_and_boot()
		self._draw_feet()
		self._draw_switch()
		self._draw_logo()
		glEndList()

	def _make_logo_texture(self):
		x0, x1, z0, z1 = self.logo_rect
		height_px = 96
		width_px = int(height_px * (x1 - x0) / (z1 - z0))
		surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
		surface.fill((0, 0, 0, 0))
		font = pygame.font.SysFont("arial", int(height_px * 0.62), bold=True, italic=True)
		name = font.render("QuickShot", True, self.logo_white)
		number = font.render(" II", True, self.logo_red)
		star_size = height_px * 0.5
		total = star_size * 1.3 + name.get_width() + number.get_width()
		left = (width_px - total) / 2
		centre_y = height_px / 2
		star_centre = (left + star_size / 2, centre_y)
		pygame.draw.polygon(surface, self.logo_red, tuple(
			(star_centre[0] + (star_size / 2 if corner % 2 == 0 else star_size / 5) * math.cos(math.radians(-90 + corner * 36)),
			 star_centre[1] + (star_size / 2 if corner % 2 == 0 else star_size / 5) * math.sin(math.radians(-90 + corner * 36)))
			for corner in range(10)))
		left += star_size * 1.3
		surface.blit(name, name.get_rect(midleft=(left, centre_y)))
		surface.blit(number, number.get_rect(midleft=(left + name.get_width(), centre_y)))
		return upload_texture(surface)

	def _body_outline(self, inset):
		return rounded_rect_outline(self.width / 2 - inset, self.depth / 2 - inset, self.corner_radius - inset)

	def _draw_body(self):
		rings = [ring(self._body_outline(inset), y) for y, inset in self.rings]
		color(self.body_color)
		draw_ring_surface(rings)
		draw_cap(rings[-1], facing_up=True)
		draw_cap(rings[0], facing_up=False)

	def _draw_groove(self):
		points = ring(self._body_outline(-0.005), self.groove_height)
		glDisable(GL_LIGHTING)
		glLineWidth(2.0)
		color(self.groove_color)
		glBegin(GL_LINE_LOOP)
		for point in points:
			glVertex3f(*point)
		glEnd()
		glEnable(GL_LIGHTING)

	def _draw_platform_and_boot(self):
		centre = (0.0, self.platform_centre_z)
		platform = [ring(rounded_rect_outline(self.platform_half_size - inset, self.platform_half_size - inset,
		                                      self.platform_radius - inset, centre=centre), self.top_y + height)
		            for height, inset in self.platform_rings]
		color(self.platform_color)
		draw_ring_surface(platform)
		draw_cap(platform[-1], facing_up=True)

		boot_bottom = self.platform_top() + 0.005
		boot = [ring(rounded_rect_outline(half_size, half_size, radius, centre=centre), boot_bottom + height)
		        for height, half_size, radius in self.boot_rings]
		color(self.boot_color)
		draw_ring_surface(boot)
		draw_cap(boot[-1], facing_up=True)

	def _draw_feet(self):
		height = self.rings[0][0]
		color(self.foot_color)
		for side_x in (-1, 1):
			for side_z in (-1, 1):
				centre = (side_x * (self.width / 2 - self.foot_inset), side_z * (self.depth / 2 - self.foot_inset))
				rings = [ring(circle_outline(self.foot_bottom_radius, centre=centre), 0.0),
				         ring(circle_outline(self.foot_bottom_radius * 0.92, centre=centre), height * 0.3),
				         ring(circle_outline(self.foot_top_radius, centre=centre), height + 0.01)]
				draw_ring_surface(rings, smooth=True)
				draw_cap(rings[0], facing_up=False)

	def _draw_switch(self):
		z0, z1, y0, y1 = self.switch_rect
		x = self.width / 2
		color(self.switch_color)
		glBegin(GL_QUADS)
		quad((x + 0.01, y0, z1), (x + 0.01, y0, z0), (x + 0.01, y1, z0), (x + 0.01, y1, z1))
		glEnd()
		knob_z = z0 + (z1 - z0) * 0.3
		color(self.body_color, 1.4)
		glBegin(GL_QUADS)
		quad((x + 0.2, y0 + 0.1, knob_z + 0.25), (x + 0.2, y0 + 0.1, knob_z - 0.25),
		     (x + 0.2, y1 - 0.1, knob_z - 0.25), (x + 0.2, y1 - 0.1, knob_z + 0.25))
		quad((x, y1 - 0.1, knob_z + 0.25), (x + 0.2, y1 - 0.1, knob_z + 0.25),
		     (x + 0.2, y1 - 0.1, knob_z - 0.25), (x, y1 - 0.1, knob_z - 0.25))
		quad((x, y0 + 0.1, knob_z - 0.25), (x + 0.2, y0 + 0.1, knob_z - 0.25),
		     (x + 0.2, y0 + 0.1, knob_z + 0.25), (x, y0 + 0.1, knob_z + 0.25))
		quad((x, y0 + 0.1, knob_z + 0.25), (x + 0.2, y0 + 0.1, knob_z + 0.25),
		     (x + 0.2, y1 - 0.1, knob_z + 0.25), (x, y1 - 0.1, knob_z + 0.25))
		quad((x + 0.2, y0 + 0.1, knob_z - 0.25), (x, y0 + 0.1, knob_z - 0.25),
		     (x, y1 - 0.1, knob_z - 0.25), (x + 0.2, y1 - 0.1, knob_z - 0.25))
		glEnd()

	def _draw_logo(self):
		x0, x1, z0, z1 = self.logo_rect
		lift = self.top_y + 0.01
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor3f(1.0, 1.0, 1.0)
		textured_quad(self._logo_texture, (x0, lift, z1), (x1, lift, z1), (x1, lift, z0), (x0, lift, z0))
		glDisable(GL_BLEND)

	def draw(self):
		glCallList(self._display_list)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)
		if self._logo_texture:
			glDeleteTextures([self._logo_texture])


class JoystickStick:
	"""The pistol grip. Local frame: origin at the pivot inside the boot, y up
	along the stick, the finger grooves facing +z (the user).

	The grip is a column of squarish ovals; their front edge dips into four
	finger grooves and both front and back grow into the head at the top."""

	def __init__(self, grip_bottom=1.0, grip_top=9.4):
		self.grip_bottom = grip_bottom
		self.grip_top = grip_top
		self.ring_step = 0.2
		self.segments = 28
		self.exponent = 2.6
		self.half_width_bottom = 1.2
		self.half_width_head = 1.35
		self.back = 1.45
		self.head_back = 1.75
		self.front = 1.55
		self.head_front = 2.25
		self.head_from = 7.0
		self.head_to = 7.9
		self.groove_count = 4
		self.groove_from = 2.0
		self.groove_pitch = 1.2
		self.groove_depth = 0.3
		self.collar_height = 0.4
		self.collar_scale = 0.8
		self.top_rounding = ((0.15, 0.96), (0.0, 0.86))
		self.neck_radius = 0.6
		self.neck_bottom = -0.6
		self.grip_color = JOYSTICK_BLACK
		self.neck_color = (28, 28, 30)
		self._display_list = None

	@staticmethod
	def _smoothstep(edge0, edge1, value):
		t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
		return t * t * (3 - 2 * t)

	def section(self, y):
		"""(half_width, front, back) of the grip's cross-section at height y."""
		head = self._smoothstep(self.head_from, self.head_to, y)
		rise = (y - self.grip_bottom) / (self.grip_top - self.grip_bottom)
		half_width = self.half_width_bottom + (self.half_width_head - self.half_width_bottom) * rise
		front = self.front + (self.head_front - self.front) * head
		groove_position = (y - self.groove_from) / self.groove_pitch
		if 0.0 <= groove_position <= self.groove_count:
			front -= self.groove_depth * math.sin(math.pi * groove_position) ** 2
		back = self.back + (self.head_back - self.back) * head
		scale = self.collar_scale + (1 - self.collar_scale) * self._smoothstep(
			self.grip_bottom, self.grip_bottom + self.collar_height, y)
		return half_width * scale, front * scale, back * scale

	def _grip_heights(self):
		levels = []
		y = self.grip_bottom
		last_full = self.grip_top - self.top_rounding[0][0] - 0.05
		while y < last_full:
			levels.append((y, 1.0))
			y += self.ring_step
		levels.append((last_full, 1.0))
		levels += [(self.grip_top - drop, scale) for drop, scale in self.top_rounding]
		return levels

	def trigger_mount(self):
		"""Front face of the head, where the trigger sits."""
		y = (self.head_to + self.grip_top) / 2 - 0.2
		return 0.0, y, self.section(y)[1]

	def top_button_mount(self):
		return 0.0, self.grip_top, 0.0

	def build(self):
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		color(self.neck_color)
		neck = [ring(circle_outline(self.neck_radius), y) for y in (self.neck_bottom, self.grip_bottom + 0.2)]
		draw_ring_surface(neck, smooth=True)

		rings = []
		for y, scale in self._grip_heights():
			half_width, front, back = self.section(y)
			rings.append(ring(superellipse_outline(half_width * scale, front * scale, back * scale,
			                                       self.segments, self.exponent), y))
		color(self.grip_color)
		draw_ring_surface(rings, smooth=True)
		draw_cap(rings[-1], facing_up=True)
		draw_cap(rings[0], facing_up=False)
		glEndList()

	def draw(self):
		glCallList(self._display_list)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)


class FireButton:
	"""A red button that slides along `press_direction` while held."""

	def __init__(self, pygame_keys, press_direction, press_depth, button_color=FIRE_RED):
		self.pygame_keys = pygame_keys
		self.press_direction = press_direction
		self.press_depth = press_depth
		self.button_color = button_color
		self.press_rate = 0.5
		self.release_rate = 0.3
		self.held = False
		self.travel = 0.0
		self._display_list = None

	def handles(self, pygame_key):
		return pygame_key in self.pygame_keys

	def build(self):
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		color(self.button_color)
		self._draw_shape()
		glEndList()

	def _draw_shape(self):
		"""Emit the button's geometry in its mount frame. Override."""

	def update(self):
		target = self.press_depth if self.held else 0.0
		rate = self.press_rate if self.held else self.release_rate
		self.travel += (target - self.travel) * rate
		if abs(self.travel - target) < 0.001:
			self.travel = target

	def draw(self):
		glPushMatrix()
		glTranslatef(*(axis * self.travel for axis in self.press_direction))
		glCallList(self._display_list)
		glPopMatrix()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)


class TriggerButton(FireButton):
	"""The index-finger trigger on the front of the head: a side profile
	extruded across the grip, pushed back into the head when pressed."""

	def __init__(self, pygame_keys=(pygame.K_SPACE,)):
		super().__init__(pygame_keys, press_direction=(0.0, 0.0, -1.0), press_depth=0.2)
		self.width = 1.3
		self.profile = ((-0.4, -0.75), (0.1, -0.9), (0.28, -0.55), (0.35, 0.05), (0.25, 0.6), (-0.4, 0.6))

	def _draw_shape(self):
		half_width = self.width / 2
		glBegin(GL_QUADS)
		for index, (z0, y0) in enumerate(self.profile):
			z1, y1 = self.profile[(index + 1) % len(self.profile)]
			quad((-half_width, y0, z0), (-half_width, y1, z1), (half_width, y1, z1), (half_width, y0, z0))
		glEnd()
		for x, points in ((half_width, self.profile), (-half_width, self.profile[::-1])):
			corners = tuple((x, y, z) for z, y in points)
			glBegin(GL_POLYGON)
			glNormal3f(*face_normal(*corners[:3]))
			for corner in corners:
				glVertex3f(*corner)
			glEnd()


class TopButton(FireButton):
	"""The thumb button capping the front of the grip's top; it sinks when pressed."""

	def __init__(self, pygame_keys=(pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_RETURN)):
		super().__init__(pygame_keys, press_direction=(0.0, -1.0, 0.0), press_depth=0.2)
		self.half_width = 1.05
		self.half_depth = 1.0
		self.centre_z = 0.75
		self.corner_radius = 0.45
		self.rings = ((-0.2, 0.0), (0.3, 0.0), (0.42, 0.08), (0.48, 0.2))

	def _draw_shape(self):
		rings = [ring(rounded_rect_outline(self.half_width - inset, self.half_depth - inset,
		                                   self.corner_radius - inset, centre=(0.0, self.centre_z)), height)
		         for height, inset in self.rings]
		draw_ring_surface(rings, smooth=True)
		draw_cap(rings[-1], facing_up=True)


class JoystickCable(Cable):
	"""Black lead ending in the female 9-pin D-sub that goes into a control port."""

	def __init__(self, path, radius=0.22, plug_scale=1 / 2.5):
		super().__init__(path, radius, cable_color=(26, 26, 26), grommet_color=(40, 40, 42),
		                 grommet_radius=0.45, grommet_length=1.0, plug_scale=plug_scale)
		self.hood_color = (48, 48, 50)
		self.socket_color = (30, 30, 32)
		self.hole_color = (120, 120, 116)
		self.hood_length = 3.4
		self.hood_width = 3.6
		self.hood_height = 1.4
		self.socket_length = 0.55
		self.socket_top_width = 2.5
		self.socket_bottom_width = 2.0
		self.socket_bottom = 0.4
		self.socket_top = 1.0

	def _draw_plug(self, entry, forward):
		point = self._plug_frame(entry, forward)
		half_width, length, height = self.hood_width / 2, self.hood_length, self.hood_height
		corners = {(a, c, h): point(a * length, (c * 2 - 1) * half_width * (1 - 0.12 * (1 - a)), h * height)
		           for a in (0, 1) for c in (0, 1) for h in (0, 1)}
		color(self.hood_color)
		glBegin(GL_QUADS)
		for face in (((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
		             ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
		             ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)),
		             ((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)),
		             ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1))):
			quad(*(corners[key] for key in face))
		glEnd()

		back, front = length, length + self.socket_length
		top_half, bottom_half = self.socket_top_width / 2, self.socket_bottom_width / 2
		low, high = self.socket_bottom, self.socket_top

		def face_points(along):
			return (point(along, -bottom_half, low), point(along, bottom_half, low),
			        point(along, top_half, high), point(along, -top_half, high))

		rear, nose = face_points(back), face_points(front)
		color(self.socket_color)
		glBegin(GL_QUADS)
		for index in range(4):
			following = (index + 1) % 4
			quad(rear[index], rear[following], nose[following], nose[index])
		quad(*nose)
		glEnd()

		color(self.hole_color)
		glBegin(GL_QUADS)
		hole = 0.07
		for count, row_height, row_half in ((5, low + (high - low) * 0.68, top_half * 0.72),
		                                    (4, low + (high - low) * 0.32, bottom_half * 0.68)):
			for index in range(count):
				across = -row_half + 2 * row_half * index / (count - 1)
				quad(point(front + 0.005, across - hole, row_height - hole), point(front + 0.005, across + hole, row_height - hole),
				     point(front + 0.005, across + hole, row_height + hole), point(front + 0.005, across - hole, row_height + hole))
		glEnd()
