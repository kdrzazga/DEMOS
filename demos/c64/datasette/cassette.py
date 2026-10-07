"""3D model of a compact cassette (the tape the Datasette plays).

Local frame (centimetres): x to the right, y up, z toward the user; the
cassette lies flat on y = 0, side A up, centred on x and z, with the tape
opening (the edge the heads touch) facing +z. The two hubs sit hub_spacing
apart - the same 4.3 cm as the Datasette's spindles - so the cassette drops
onto them in the compartment.

The shell is a ring stack; each face is one painted texture (screws, label,
window with the tape packs, the lighter trapezoid with its holes) mapped onto
the flat cap; the window is smoky, half-transparent glass in that texture, so the
inside shows through. The two white hubs (the cog wheels the spindles drive)
and the two tape rolls wound on them are separate items: ``CassetteHub`` turns,
``TapeRoll`` grows or shrinks with ``Cassette.roll_position``.
"""

import math

import pygame
from OpenGL.GL import *

from demos.c64.geometry import color, quad, upload_texture
from demos.c64.surfaces import draw_ring_surface, ring, rounded_rect_outline


class CassetteHub:
	"""One white hub: a ring with drive teeth inside, seen on both faces.

	Local frame: origin at the hub's axis, half-way through the cassette;
	the faces are at +-face_offset. turns rotates it about y; positive turns
	go counter-clockwise seen from side A."""

	def __init__(self, face_offset, outer_radius=0.6, inner_radius=0.45, tooth_radius=0.3, tooth_count=6,
	             hub_color=(238, 238, 232)):
		self.face_offset = face_offset
		self.outer_radius = outer_radius
		self.inner_radius = inner_radius
		self.tooth_radius = tooth_radius
		self.tooth_count = tooth_count
		self.tooth_half_width = 0.06
		self.ring_segments = 32
		self.hub_color = hub_color
		self.turns = 0.0
		self._display_list = None

	def turn(self, turns):
		self.turns += turns

	def build(self):
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		color(self.hub_color)
		self._draw_face(self.face_offset, facing_up=True)
		self._draw_face(-self.face_offset, facing_up=False)
		glEndList()

	def _draw_face(self, y, facing_up):
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0 if facing_up else -1.0, 0.0)
		for step in range(self.ring_segments):
			a0, a1 = 2 * math.pi * step / self.ring_segments, 2 * math.pi * (step + 1) / self.ring_segments
			corners = [(radius * math.cos(angle), y, radius * math.sin(angle))
			           for radius, angle in ((self.inner_radius, a0), (self.inner_radius, a1),
			                                 (self.outer_radius, a1), (self.outer_radius, a0))]
			for corner in (corners if facing_up else corners[::-1]):
				glVertex3f(*corner)
		for tooth in range(self.tooth_count):
			angle = tooth * 2 * math.pi / self.tooth_count
			radial_x, radial_z = math.cos(angle), math.sin(angle)
			side_x, side_z = -radial_z * self.tooth_half_width, radial_x * self.tooth_half_width
			inner, outer = self.tooth_radius, self.inner_radius + 0.01
			corners = [(radial_x * inner - side_x, y, radial_z * inner - side_z),
			           (radial_x * inner + side_x, y, radial_z * inner + side_z),
			           (radial_x * outer + side_x, y, radial_z * outer + side_z),
			           (radial_x * outer - side_x, y, radial_z * outer - side_z)]
			for corner in (corners if facing_up else corners[::-1]):
				glVertex3f(*corner)
		glEnd()

	def draw(self):
		glPushMatrix()
		glRotatef(self.turns * 360.0, 0.0, 1.0, 0.0)
		glCallList(self._display_list)
		glPopMatrix()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)


class TapeRoll:
	"""The tape wound on one hub: a brown disc around the hub. Its area is
	proportional to the share of the tape on this reel, so the radius follows
	the square root. Local frame: origin at the hub's axis, half-way through
	the cassette."""

	def __init__(self, core_radius=0.6, full_radius=2.05, tape_width=0.38, tape_color=(84, 56, 38)):
		self.core_radius = core_radius
		self.full_radius = full_radius
		self.tape_width = tape_width
		self.tape_color = tape_color
		self.segments = 48
		self.share = 0.0

	def radius_for(self, share):
		"""Outer radius when this reel holds `share` of the tape (0 = empty, 1 = all of it)."""
		core_squared = self.core_radius ** 2
		return math.sqrt(core_squared + share * (self.full_radius ** 2 - core_squared))

	def radius(self):
		return self.radius_for(self.share)

	def draw(self):
		outer, inner = self.radius(), self.core_radius
		if outer - inner < 0.005:
			return
		half_width = self.tape_width / 2
		angles = [2 * math.pi * step / self.segments for step in range(self.segments + 1)]
		color(self.tape_color)
		glBegin(GL_QUADS)
		for a0, a1 in zip(angles, angles[1:]):
			c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
			glNormal3f(0.0, 1.0, 0.0)
			for radius, cosine, sine in ((inner, c0, s0), (inner, c1, s1), (outer, c1, s1), (outer, c0, s0)):
				glVertex3f(radius * cosine, half_width, radius * sine)
			glNormal3f(0.0, -1.0, 0.0)
			for radius, cosine, sine in ((outer, c0, s0), (outer, c1, s1), (inner, c1, s1), (inner, c0, s0)):
				glVertex3f(radius * cosine, -half_width, radius * sine)
			for cosine, sine, height in ((c0, s0, -half_width), (c1, s1, -half_width),
			                             (c1, s1, half_width), (c0, s0, half_width)):
				glNormal3f(cosine, 0.0, sine)
				glVertex3f(outer * cosine, height, outer * sine)
		glEnd()


class Cassette:

	def __init__(self, title="COMMODORE 64", width=10.04, depth=6.38, thickness=1.2, hub_spacing=4.3,
	             length_minutes=60.0, roll_position=0.0, tape_cm_per_minute=285.6):
		self.title = title
		self.length_minutes = length_minutes
		self.tape_cm_per_minute = tape_cm_per_minute
		self.width = width
		self.depth = depth
		self.thickness = thickness
		self.hub_spacing = hub_spacing
		self.corner_radius = 0.35
		self.edge_bevel = 0.06
		self.texture_px_per_cm = 100

		self.shell_color = (40, 40, 42)
		self.screw_color = (96, 96, 98)
		self.screw_slot_color = (30, 30, 30)
		self.label_color = (232, 226, 206)
		self.label_ink = (52, 46, 40)
		self.window_color = (26, 22, 20)
		self.window_alpha = 70
		self.window_rim_color = (196, 194, 188)
		self.tape_color = (84, 56, 38)
		self.lip_color = (182, 178, 168)
		self.hole_color = (18, 18, 18)

		self.hub_z = -0.45
		self.hub_window_radius = 0.8
		self.window_rect = (-1.35, 1.35, -0.95, 0.05)
		self.label_rect = (-4.4, 4.4, -2.65, 1.25)
		self.label_stripes = ((0.45, 0.55), (0.66, 0.72), (0.82, 0.86))
		self.screw_positions = ((-4.55, -2.7), (4.55, -2.7), (-4.4, 2.6), (4.4, 2.6))
		self.screw_radius = 0.22
		self.top_hole = (0.0, -2.95, 0.08)
		self.lip_front_half_width = 3.75
		self.lip_back_half_width = 3.2
		self.lip_back_z = 1.6
		self.lip_holes = ((-2.45, 2.6, 0.2), (-1.35, 2.6, 0.18), (1.35, 2.6, 0.18), (2.45, 2.6, 0.2))
		self.lip_screw = (0.0, 2.05, 0.15)
		self.front_openings = ((-3.4, -2.4), (-1.9, -1.5), (-0.6, 0.6), (1.5, 1.9), (2.4, 3.4))
		self.front_opening_height = (0.3, 0.9)

		self.left_hub = CassetteHub(face_offset=thickness / 2 - 0.08)
		self.right_hub = CassetteHub(face_offset=thickness / 2 - 0.08)
		self.hubs = (self.left_hub, self.right_hub)
		self.left_roll = TapeRoll(core_radius=self.left_hub.outer_radius, tape_color=self.tape_color)
		self.right_roll = TapeRoll(core_radius=self.right_hub.outer_radius, tape_color=self.tape_color)
		self.rolls = (self.left_roll, self.right_roll)
		self.roll_position = roll_position
		self._display_list = None
		self._textures = []

	def hub_centres(self):
		return (-self.hub_spacing / 2, self.hub_z), (self.hub_spacing / 2, self.hub_z)

	@property
	def roll_position(self):
		"""Minutes of tape wound onto the right reel: 0 = all on the left hub,
		length_minutes / 2 = equal rolls, length_minutes = all on the right hub."""
		return self._roll_position

	@roll_position.setter
	def roll_position(self, minutes):
		self._roll_position = max(0.0, min(self.length_minutes, minutes))
		right_share = self._roll_position / self.length_minutes
		self.left_roll.share = 1.0 - right_share
		self.right_roll.share = right_share

	def wind(self, minutes):
		"""Move the tape by `minutes` (negative rewinds), stopping at either end.
		Each hub turns by the tape length over its roll's circumference, so the
		filling reel slows down and the emptying one speeds up. Returns the
		minutes actually moved."""
		start = self.roll_position
		self.roll_position = start + minutes
		moved = self.roll_position - start
		if moved:
			right_share = (start + moved / 2) / self.length_minutes
			for hub, roll, share in ((self.left_hub, self.left_roll, 1.0 - right_share),
			                         (self.right_hub, self.right_roll, right_share)):
				hub.turn(moved * self.tape_cm_per_minute / (2 * math.pi * roll.radius_for(share)))
		return moved

	def build(self):
		"""Create the face textures and the shell display list. Needs a GL context."""
		self._side_a_texture = upload_texture(self._paint_face("A"))
		self._side_b_texture = upload_texture(self._paint_face("B"))
		self._textures = [self._side_a_texture, self._side_b_texture]
		for hub in self.hubs:
			hub.build()
		self._display_list = glGenLists(2)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_shell()
		self._draw_front_openings()
		glEndList()
		glNewList(self._display_list + 1, GL_COMPILE)
		self._draw_faces()
		glEndList()

	def _to_px(self, x, z):
		scale = self.texture_px_per_cm
		return (x + self.width / 2) * scale, (z + self.depth / 2) * scale

	def _paint_face(self, side_letter):
		"""One face as seen from outside, tape opening at the bottom of the image."""
		scale = self.texture_px_per_cm
		surface = pygame.Surface((int(self.width * scale), int(self.depth * scale)), pygame.SRCALPHA)
		surface.fill(self.shell_color)

		x0, x1, z0, z1 = self.label_rect
		left, top = self._to_px(x0, z0)
		right, bottom = self._to_px(x1, z1)
		label = pygame.Rect(left, top, right - left, bottom - top)
		pygame.draw.rect(surface, self.label_color, label, border_radius=int(0.2 * scale))
		pygame.draw.line(surface, self.label_ink, self._to_px(x0 + 0.2, z0 + 0.3), self._to_px(x1 - 0.2, z0 + 0.3), 3)
		title_font = pygame.font.SysFont("arial", int(0.42 * scale), bold=True)
		title = title_font.render(self.title, True, self.label_ink)
		surface.blit(title, title.get_rect(center=self._to_px(0.0, z0 + 0.72)))
		letter_font = pygame.font.SysFont("arial", int(0.6 * scale), bold=True)
		for letter_x in (x0 + 0.65, x1 - 0.65):
			letter = letter_font.render(side_letter, True, self.label_ink)
			surface.blit(letter, letter.get_rect(center=self._to_px(letter_x, self.hub_z)))
		for stripe_z0, stripe_z1 in self.label_stripes:
			stripe_left, stripe_top = self._to_px(x0, stripe_z0)
			stripe_right, stripe_bottom = self._to_px(x1, stripe_z1)
			pygame.draw.rect(surface, self.label_ink, pygame.Rect(stripe_left, stripe_top, stripe_right - stripe_left,
			                                                       stripe_bottom - stripe_top))

		self._cut_window(surface)

		lip = (self._to_px(-self.lip_front_half_width, self.depth / 2), self._to_px(self.lip_front_half_width, self.depth / 2),
		       self._to_px(self.lip_back_half_width, self.lip_back_z), self._to_px(-self.lip_back_half_width, self.lip_back_z))
		pygame.draw.polygon(surface, self.lip_color, lip)
		for hole_x, hole_z, radius in self.lip_holes:
			pygame.draw.circle(surface, self.hole_color, self._to_px(hole_x, hole_z), radius * scale)
		self._paint_screw(surface, *self.lip_screw)
		for screw_x, screw_z in self.screw_positions:
			self._paint_screw(surface, screw_x, screw_z, self.screw_radius)
		hole_x, hole_z, radius = self.top_hole
		pygame.draw.circle(surface, self.hole_color, self._to_px(hole_x, hole_z), radius * scale)
		return surface

	def _cut_window(self, surface):
		"""Replace the window - two round hub windows joined by the middle slot -
		with smoky glass (window_color at window_alpha), then ring the hub windows."""
		scale = self.texture_px_per_cm
		window_x0, window_x1, window_z0, window_z1 = self.window_rect
		glass = (*self.window_color, self.window_alpha)
		left, top = self._to_px(window_x0, window_z0)
		right, bottom = self._to_px(window_x1, window_z1)
		pygame.draw.rect(surface, glass, pygame.Rect(left, top, right - left, bottom - top), border_radius=int(0.15 * scale))
		for hub_x, hub_z in self.hub_centres():
			pygame.draw.circle(surface, glass, self._to_px(hub_x, hub_z), self.hub_window_radius * scale)
		for hub_x, hub_z in self.hub_centres():
			pygame.draw.circle(surface, self.window_rim_color, self._to_px(hub_x, hub_z), self.hub_window_radius * scale, 4)

	def _paint_screw(self, surface, centre_x, centre_z, radius):
		scale = self.texture_px_per_cm
		centre = self._to_px(centre_x, centre_z)
		pygame.draw.circle(surface, self.screw_color, centre, radius * scale)
		slot = radius * scale * 0.7
		pygame.draw.line(surface, self.screw_slot_color, (centre[0] - slot, centre[1]), (centre[0] + slot, centre[1]), 3)
		pygame.draw.line(surface, self.screw_slot_color, (centre[0], centre[1] - slot), (centre[0], centre[1] + slot), 3)

	def _outline(self, inset):
		return rounded_rect_outline(self.width / 2 - inset, self.depth / 2 - inset, self.corner_radius - inset, corner_segments=4)

	def _draw_shell(self):
		bevel, thickness = self.edge_bevel, self.thickness
		rings = [ring(self._outline(bevel), 0.0), ring(self._outline(0.0), bevel),
		         ring(self._outline(0.0), thickness - bevel), ring(self._outline(bevel), thickness)]
		color(self.shell_color)
		draw_ring_surface(rings)

	def _draw_faces(self):
		"""Both textured faces; drawn last and blended, so the smoky window
		shows the hubs and tape rolls inside."""
		bevel = self.edge_bevel
		self._textured_cap(ring(self._outline(bevel), self.thickness), self._side_a_texture, facing_up=True)
		self._textured_cap(ring(self._outline(bevel), 0.0), self._side_b_texture, facing_up=False)

	def _textured_cap(self, points, texture, facing_up):
		"""Flat face with the face texture laid over the cassette's footprint.
		Side B is seen with the cassette turned over left-to-right, so its
		texture runs from +x to -x."""
		if facing_up:
			points = points[::-1]
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, texture)
		glColor3f(1.0, 1.0, 1.0)
		glBegin(GL_POLYGON)
		glNormal3f(0.0, 1.0 if facing_up else -1.0, 0.0)
		for x, y, z in points:
			across = (x + self.width / 2) / self.width
			glTexCoord2f(across if facing_up else 1.0 - across, 1.0 - (z + self.depth / 2) / self.depth)
			glVertex3f(x, y, z)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def _draw_front_openings(self):
		front = self.depth / 2 + 0.005
		low, high = self.front_opening_height
		tape_low, tape_high = low + 0.12, high - 0.12
		glBegin(GL_QUADS)
		for x0, x1 in self.front_openings:
			color(self.hole_color)
			quad((x0, low, front), (x1, low, front), (x1, high, front), (x0, high, front))
			color(self.tape_color)
			quad((x0, tape_low, front + 0.003), (x1, tape_low, front + 0.003),
			     (x1, tape_high, front + 0.003), (x0, tape_high, front + 0.003))
		glEnd()

	def draw(self):
		glCallList(self._display_list)
		for hub, roll, (centre_x, centre_z) in zip(self.hubs, self.rolls, self.hub_centres()):
			glPushMatrix()
			glTranslatef(centre_x, self.thickness / 2, centre_z)
			roll.draw()
			hub.draw()
			glPopMatrix()
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glCallList(self._display_list + 1)
		glDisable(GL_BLEND)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 2)
		for hub in self.hubs:
			hub.destroy()
		if self._textures:
			glDeleteTextures(self._textures)
