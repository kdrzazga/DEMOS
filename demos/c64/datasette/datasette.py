"""3D model of the Commodore Datasette (C2N / 1530 cassette recorder).

Proportions come from the photos in resources/ (front, top, side,
bottom). The separate parts - piano keys, cassette door, counter with its reset
button, cable - live in datasette_parts.py; this class builds the case and
assembles them on it.

World frame (centimetres): x to the right, y up, z toward the user, the same
as the Commodore64 model. The case is centred on x and z and stands on y = 0.

The case is a stack of rounded-rectangle rings (plan outline at a height, inset
by the edge rounding). Above the base's top ledge the rings are notched at the
front-left: that notch is the button bay the six keys sit in. The cassette
compartment is a hole in the flat top under the door.
"""

import math
import os

import pygame
from OpenGL.GL import *

from demos.c64.datasette.datasette_parts import (ButtonEject, ButtonFastForward, ButtonPlay, ButtonRecord,
                                                 ButtonRewind, ButtonStop, CassetteDoor, DatasetteCable, LABEL_INK,
                                                 TapeCounter)
from demos.c64.geometry import color, image_texture, textured_quad, upload_texture


class Datasette:

	def __init__(self, width=19.0, depth=15.5, corner_radius=2.4,
	             rings=((0.0, 0.45, False), (0.105, 0.15, False), (0.315, 0.0, False), (1.295, 0.0, False),
	                    (1.47, 0.08, False), (1.54, 0.22, False), (1.54, 0.3, False), (1.54, 0.3, True),
	                    (3.185, 0.3, True), (3.465, 0.42, True), (3.64, 0.62, True), (3.745, 0.85, True),
	                    (3.794, 1.05, True))):
		self.width = width
		self.depth = depth
		self.corner_radius = corner_radius
		self.rings = rings
		self.arc_segments = 8
		self.top_y = rings[-1][0]
		self.top_inset = rings[-1][1]
		self.bay_floor = next(y for y, _, notched in rings if notched)
		self.bay_left = -6.9
		self.bay_right = 2.9
		self.bay_back = 4.55

		self.case_color = (226, 214, 166)
		self.bay_shade = 0.8

		self.door_hinge = (-2.0, -4.8)
		self.compartment_margin = 0.1

		self.nameplate_rect = (-7.6, 4.2, 2.55, 3.85)
		self.nameplate_silver = (186, 188, 192)
		self.nameplate_ink = (16, 16, 16)
		self.nameplate_stripe_count = 7
		self.label_depth = (3.92, 4.48)
		self.texture_px_per_cm = 90
		self.bottom_label_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "label.png")
		self.bottom_label_area_fraction = 1 / 8 * 0.75 ** 2

		self.counter_centre = (5.6, 3.2)
		self.led_centre = (5.6, 4.65)
		self.led_radius = 0.17
		self.led_lit_color = (255, 40, 30)
		self.led_dark_color = (96, 22, 18)

		self.cable_path = ((-5.5, 0.84, -7.75), (-5.5, 0.8, -8.7), (-5.9, 0.45, -10.1), (-7.6, 0.26, -11.7),
		                   (-11.0, 0.26, -12.4), (-14.0, 0.26, -10.6), (-15.0, 0.26, -6.6),
		                   (-14.2, 0.35, -3.0), (-13.0, 0.55, -0.6))

		self.play_counts_per_second = 1.2
		self.wind_counts_per_second = 12.0
		self.play_hub_turns_per_second = 0.5
		self.wind_hub_turns_per_second = 4.0

		self.record_button = ButtonRecord()
		self.play_button = ButtonPlay()
		self.rewind_button = ButtonRewind()
		self.fast_forward_button = ButtonFastForward()
		self.stop_button = ButtonStop()
		self.eject_button = ButtonEject()
		self.buttons = (self.record_button, self.play_button, self.rewind_button,
		                self.fast_forward_button, self.stop_button, self.eject_button)
		self.door = CassetteDoor(width=self.bay_right - self.bay_left, depth=self.nameplate_rect[2] - 0.15 - self.door_hinge[1])
		self.counter = TapeCounter()
		self.cable = DatasetteCable(self.cable_path)

		self.led_on = False
		self._last_ticks = None
		self._display_list = None
		self._textures = []


	def button_centre_x(self, index):
		pitch = (self.bay_right - self.bay_left) / len(self.buttons)
		return self.bay_left + (index + 0.5) * pitch

	def _outline(self, inset, notched):
		"""Plan outline (x, z) of one ring: the rounded rectangle shrunk by inset,
		clockwise from above, ending with four points on the front edge that are
		either the button bay or (unnotched) collapsed onto the front edge."""
		half_width = self.width / 2 - inset
		half_depth = self.depth / 2 - inset
		radius = self.corner_radius - inset
		points = []
		for (centre_x, centre_z), start_degrees in (((-half_width + radius, half_depth - radius), 90),
		                                            ((-half_width + radius, -half_depth + radius), 180),
		                                            ((half_width - radius, -half_depth + radius), 270),
		                                            ((half_width - radius, half_depth - radius), 0)):
			for step in range(self.arc_segments + 1):
				angle = math.radians(start_degrees + 90 * step / self.arc_segments)
				points.append((centre_x + radius * math.cos(angle), centre_z + radius * math.sin(angle)))
		bay_back = self.bay_back if notched else half_depth
		points += [(self.bay_right, half_depth), (self.bay_right, bay_back),
		           (self.bay_left, bay_back), (self.bay_left, half_depth)]
		return points

	def _holes(self):
		"""Rectangles (x0, x1, z0, z1) missing from the flat top: the cassette
		compartment and the button bay (which runs out past the front edge)."""
		margin = self.compartment_margin
		hinge_z = self.door_hinge[1]
		return ((self.bay_left + margin, self.bay_right - margin, hinge_z + margin, hinge_z + self.door.depth - margin),
		        (self.bay_left, self.bay_right, self.bay_back, self.depth))

	def _top_pieces(self):
		"""The top outline minus the holes, as convex polygons: cut into strips
		along z at every hole edge, then each strip into the x spans between holes."""
		outline = self._outline(self.top_inset, notched=False)
		holes = self._holes()
		far = self.width + self.depth
		z_cuts = sorted({-far, far, *(edge for hole in holes for edge in hole[2:])})
		pieces = []
		for z0, z1 in zip(z_cuts, z_cuts[1:]):
			centre_z = (z0 + z1) / 2
			active = [hole for hole in holes if hole[2] < centre_z < hole[3]]
			x_cuts = sorted({-far, far, *(edge for hole in active for edge in hole[:2])})
			for x0, x1 in zip(x_cuts, x_cuts[1:]):
				centre_x = (x0 + x1) / 2
				if any(hole[0] < centre_x < hole[1] for hole in active):
					continue
				piece = outline
				for axis, value, keep_greater in ((0, x0, True), (0, x1, False), (1, z0, True), (1, z1, False)):
					piece = self._clip(piece, axis, value, keep_greater)
				if len(piece) >= 3:
					pieces.append(piece)
		return pieces

	@staticmethod
	def _clip(polygon, axis, value, keep_greater):
		"""Sutherland-Hodgman: keep the part of a convex polygon on one side of
		the line where coordinate `axis` equals `value`."""
		def inside(point):
			return point[axis] >= value if keep_greater else point[axis] <= value

		kept = []
		for index, current in enumerate(polygon):
			previous = polygon[index - 1]
			if inside(current) != inside(previous):
				t = (value - previous[axis]) / (current[axis] - previous[axis])
				kept.append(tuple(p + (c - p) * t for p, c in zip(previous, current)))
			if inside(current):
				kept.append(current)
		return kept


	def build(self):
		"""Create textures and display lists for the case and every part. Needs a GL context."""
		for button in self.buttons:
			button.build()
		self.door.build()
		self.counter.build()
		self.cable.build()

		self._nameplate_texture = self._make_nameplate_texture()
		self._labels_texture = self._make_labels_texture()
		self._bottom_label_texture, self._bottom_label_aspect = image_texture(self.bottom_label_image)
		self._textures = [self._nameplate_texture, self._labels_texture, self._bottom_label_texture]

		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_shell()
		self._draw_top()
		self._draw_bottom()
		self._draw_bottom_label()
		self._draw_nameplate_and_labels()
		glEndList()

	def _make_nameplate_texture(self):
		x0, x1, z0, z1 = self.nameplate_rect
		width_px, height_px = int((x1 - x0) * self.texture_px_per_cm), int((z1 - z0) * self.texture_px_per_cm)
		surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
		surface.fill(self.nameplate_silver)
		ink = self.nameplate_ink

		centre_x, centre_y = height_px * 0.6, height_px / 2
		outer, inner = height_px * 0.36, height_px * 0.2
		pygame.draw.circle(surface, ink, (centre_x, centre_y), outer)
		pygame.draw.circle(surface, self.nameplate_silver, (centre_x, centre_y), inner)
		pygame.draw.rect(surface, self.nameplate_silver, pygame.Rect(centre_x, centre_y - inner, outer + 2, 2 * inner))
		gap, slant = inner * 0.12, inner * 0.6
		pygame.draw.polygon(surface, ink, ((centre_x + gap, centre_y - inner), (centre_x + outer + slant, centre_y - inner),
		                                   (centre_x + outer, centre_y - gap), (centre_x + gap, centre_y - gap)))
		pygame.draw.polygon(surface, ink, ((centre_x + gap, centre_y + gap), (centre_x + outer, centre_y + gap),
		                                   (centre_x + outer + slant, centre_y + inner), (centre_x + gap, centre_y + inner)))

		font = pygame.font.SysFont("arial", int(height_px * 0.62), bold=True)
		text = font.render("commodore", True, ink)
		surface.blit(text, text.get_rect(midleft=(centre_x + outer + slant + inner * 0.6, centre_y)))

		stripes_left, stripes_right = width_px * 0.8, width_px * 0.985
		stripe_pitch = (stripes_right - stripes_left) / (self.nameplate_stripe_count - 0.4)
		for index in range(self.nameplate_stripe_count):
			left = stripes_left + index * stripe_pitch
			pygame.draw.rect(surface, ink, pygame.Rect(left, height_px * 0.1, stripe_pitch * 0.6, height_px * 0.8))
		pygame.draw.rect(surface, (120, 122, 126), surface.get_rect(), 2)
		return upload_texture(surface)

	def _make_labels_texture(self):
		near_z, far_z = self.label_depth
		width_px = int((self.bay_right - self.bay_left) * self.texture_px_per_cm)
		height_px = int((far_z - near_z) * self.texture_px_per_cm)
		surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
		surface.fill((0, 0, 0, 0))
		font = pygame.font.SysFont("arial", int(height_px * 0.5), bold=True)
		for index, button in enumerate(self.buttons):
			centre_px = (self.button_centre_x(index) - self.bay_left) * self.texture_px_per_cm
			button.paint_label(surface, centre_px, height_px / 2, font, LABEL_INK)
		return upload_texture(surface)

	@staticmethod
	def _wall_quad(p0, p1, p2, p3):
		"""Quad whose normal comes from its diagonals, so a quad with two
		coincident corners (a triangle) still lights; fully flat ones are skipped."""
		ax, ay, az = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
		bx, by, bz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
		nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
		length = math.sqrt(nx * nx + ny * ny + nz * nz)
		if length < 1e-9:
			return
		glNormal3f(nx / length, ny / length, nz / length)
		for corner in (p0, p1, p2, p3):
			glVertex3f(*corner)

	def _draw_shell(self):
		outlines = [(y, notched, self._outline(inset, notched)) for y, inset, notched in self.rings]
		bay_from = len(outlines[0][2]) - 4
		glBegin(GL_QUADS)
		for (y0, _, lower), (y1, upper_notched, upper) in zip(outlines, outlines[1:]):
			for index in range(len(lower)):
				following = (index + 1) % len(lower)
				in_bay = upper_notched and index >= bay_from and following >= bay_from
				color(self.case_color, self.bay_shade if in_bay else 1.0)
				(ax, az), (bx, bz) = lower[index], lower[following]
				(cx, cz), (dx, dz) = upper[following], upper[index]
				self._wall_quad((ax, y0, az), (bx, y0, bz), (cx, y1, cz), (dx, y1, dz))
		glEnd()

	def _flat_polygon(self, points, y, facing_up):
		"""Horizontal polygon from (x, z) points, wound to face up or down."""
		signed_area = sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(points, points[1:] + points[:1]))
		if (signed_area < 0) != facing_up:
			points = points[::-1]
		glBegin(GL_POLYGON)
		glNormal3f(0.0, 1.0 if facing_up else -1.0, 0.0)
		for x, z in points:
			glVertex3f(x, y, z)
		glEnd()

	def _draw_top(self):
		color(self.case_color)
		for piece in self._top_pieces():
			self._flat_polygon(piece, self.top_y, facing_up=True)

	def _draw_bottom(self):
		y, inset, _ = self.rings[0]
		color(self.case_color, 0.7)
		self._flat_polygon(self._outline(inset, notched=False)[:-4], y, facing_up=False)

	def _draw_bottom_label(self):
		"""The serial-number sticker in the middle of the base, covering
		bottom_label_area_fraction of it; it reads with the recorder turned over
		toward the viewer (top of the text toward the front)."""
		y, inset, _ = self.rings[0]
		outline = self._outline(inset, notched=False)[:-4]
		base_area = abs(sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(outline, outline[1:] + outline[:1]))) / 2
		label_depth = math.sqrt(base_area * self.bottom_label_area_fraction / self._bottom_label_aspect)
		half_width, half_depth, below = label_depth * self._bottom_label_aspect / 2, label_depth / 2, y - 0.01
		glColor3f(1.0, 1.0, 1.0)
		textured_quad(self._bottom_label_texture, (-half_width, below, -half_depth), (half_width, below, -half_depth),
		              (half_width, below, half_depth), (-half_width, below, half_depth))

	def _draw_nameplate_and_labels(self):
		lift = self.top_y + 0.01
		x0, x1, z0, z1 = self.nameplate_rect
		glColor3f(1.0, 1.0, 1.0)
		textured_quad(self._nameplate_texture, (x0, lift, z1), (x1, lift, z1), (x1, lift, z0), (x0, lift, z0))
		near_z, far_z = self.label_depth
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		textured_quad(self._labels_texture, (self.bay_left, lift, far_z), (self.bay_right, lift, far_z),
		              (self.bay_right, lift, near_z), (self.bay_left, lift, near_z))
		glDisable(GL_BLEND)

	def _draw_led(self):
		centre_x, centre_z = self.led_centre
		y = self.top_y + 0.015
		glDisable(GL_LIGHTING)
		color(self.led_lit_color if self.led_on else self.led_dark_color)
		glBegin(GL_TRIANGLE_FAN)
		glVertex3f(centre_x, y, centre_z)
		for step in range(21):
			angle = 2 * math.pi * step / 20
			glVertex3f(centre_x + self.led_radius * math.cos(angle), y, centre_z + self.led_radius * math.sin(angle))
		glEnd()
		glEnable(GL_LIGHTING)


	def press(self, pygame_key, is_down):
		for button in self.buttons:
			if button.handles(pygame_key):
				button.held = is_down
				if is_down:
					self._operate(button)
		if self.counter.handles(pygame_key):
			self.counter.press_reset(is_down)

	def _operate(self, button):
		"""The transport mechanics: RECORD, PLAY, REWIND and F.FWD lock down
		(RECORD takes PLAY with it) and release each other; STOP releases them;
		EJECT releases them too, and opens or closes the door when the tape was
		already stopped."""
		was_running = any(other.latched for other in self.buttons)
		for other in self.buttons:
			other.latched = False
		if button.latching:
			button.latched = True
			if button is self.record_button:
				self.play_button.latched = True
		elif button is self.eject_button and not was_running:
			self.door.toggle()

	def _transport_speeds(self):
		"""(counter counts, hub turns) per second for the latched function."""
		if self.fast_forward_button.latched:
			return self.wind_counts_per_second, self.wind_hub_turns_per_second
		if self.rewind_button.latched:
			return -self.wind_counts_per_second, -self.wind_hub_turns_per_second
		if self.play_button.latched:
			return self.play_counts_per_second, self.play_hub_turns_per_second
		return 0.0, 0.0

	def update(self):
		ticks = pygame.time.get_ticks()
		seconds = 0.0 if self._last_ticks is None else min((ticks - self._last_ticks) / 1000.0, 0.1)
		self._last_ticks = ticks

		counts_per_second, hub_turns_per_second = self._transport_speeds()
		self.counter.advance(counts_per_second * seconds)
		self.counter.update()
		self.door.update(hub_turns_per_second * seconds)
		for button in self.buttons:
			button.update()
		self.led_on = self.record_button.latched

	def draw_case(self):
		glCallList(self._display_list)

	def draw(self):
		self.draw_case()
		for index, button in enumerate(self.buttons):
			glPushMatrix()
			glTranslatef(self.button_centre_x(index), self.bay_floor, self.bay_back)
			button.draw()
			glPopMatrix()

		counter_x, counter_z = self.counter_centre
		glPushMatrix()
		glTranslatef(counter_x, self.top_y, counter_z)
		self.counter.draw()
		glPopMatrix()

		self._draw_led()
		self.cable.draw()

		hinge_x, hinge_z = self.door_hinge
		glPushMatrix()
		glTranslatef(hinge_x, self.top_y, hinge_z)
		self.door.draw()
		glPopMatrix()

	def destroy(self):
		for part in (*self.buttons, self.door, self.counter, self.cable):
			part.destroy()
		if self._display_list:
			glDeleteLists(self._display_list, 1)
		if self._textures:
			glDeleteTextures(self._textures)
