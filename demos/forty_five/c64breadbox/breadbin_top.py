import math

import pygame
from OpenGL.GL import *

from demos.forty_five.c64breadbox.opening_face import OpeningFace
from demos.forty_five.geometry import color, quad, upload_texture


class KeyboardFace:

	def __init__(self, half_width, slope_length, holes, hole_wall_depth):
		self.half_width = half_width
		self.slope_length = slope_length
		self.holes = holes
		self.hole_wall_depth = hole_wall_depth

	def _is_hole(self, xs, zs, column, row):
		if column < 0 or row < 0 or column >= len(xs) - 1 or row >= len(zs) - 1:
			return False
		centre_x, centre_z = (xs[column] + xs[column + 1]) / 2, (zs[row] + zs[row + 1]) / 2
		return any(x0 < centre_x < x1 and z0 < centre_z < z1 for x0, x1, z0, z1 in self.holes)

	def draw(self, rgb, wall_shade):
		xs = sorted({-self.half_width, self.half_width, *(edge for hole in self.holes for edge in hole[:2])})
		zs = sorted({-self.slope_length, 0.0, *(edge for hole in self.holes for edge in hole[2:])})
		cells = [(column, row) for column in range(len(xs) - 1) for row in range(len(zs) - 1)]
		depth = -self.hole_wall_depth

		color(rgb)
		glBegin(GL_QUADS)
		for column, row in cells:
			if not self._is_hole(xs, zs, column, row):
				x0, x1, z0, z1 = xs[column], xs[column + 1], zs[row], zs[row + 1]
				quad((x0, 0.0, z1), (x1, 0.0, z1), (x1, 0.0, z0), (x0, 0.0, z0))
		glEnd()

		color(rgb, wall_shade)
		glBegin(GL_QUADS)
		for column, row in cells:
			if not self._is_hole(xs, zs, column, row):
				continue
			x0, x1, z0, z1 = xs[column], xs[column + 1], zs[row], zs[row + 1]
			if not self._is_hole(xs, zs, column - 1, row):
				quad((x0, 0.0, z0), (x0, 0.0, z1), (x0, depth, z1), (x0, depth, z0))
			if not self._is_hole(xs, zs, column + 1, row):
				quad((x1, 0.0, z1), (x1, 0.0, z0), (x1, depth, z0), (x1, depth, z1))
			if not self._is_hole(xs, zs, column, row - 1):
				quad((x1, 0.0, z0), (x0, 0.0, z0), (x0, depth, z0), (x1, depth, z0))
			if not self._is_hole(xs, zs, column, row + 1):
				quad((x0, 0.0, z1), (x1, 0.0, z1), (x1, depth, z1), (x0, depth, z1))
		glEnd()


class BreadbinTop:

	def __init__(self, layout, keyboard):
		self.layout = layout
		self.keyboard = keyboard
		self.half_width = layout.width_cm / 2
		self.half_depth = layout.depth_cm / 2
		self.wall = layout.wall_thickness_cm
		self.seam = layout.seam_height_cm
		self.profile = layout.top_profile
		self.key_sink = 0.5
		self.hole_margin = 0.15
		self.hole_wall_depth = 0.35
		self.hole_wall_shade = 0.75
		self.tunnel_shade = 0.6
		slope_front_z, slope_front_y = self.profile[layout.keyboard_slope_edge]
		slope_back_z, slope_back_y = self.profile[layout.keyboard_slope_edge + 1]
		self.slope_origin = (slope_front_z, slope_front_y)
		self.slope_length = math.hypot(slope_front_z - slope_back_z, slope_back_y - slope_front_y)
		self.slope_degrees = math.degrees(math.atan2(slope_back_y - slope_front_y, slope_front_z - slope_back_z))
		self.keyboard_origin = (0.0, -self.key_sink, -(self.slope_length - layout.keyboard_back_inset_cm))
		self.keyboard_face = KeyboardFace(self.half_width, self.slope_length, self._holes_in_face_frame(),
		                                  self.hole_wall_depth)
		self.front_face = OpeningFace(-self.half_width, self.half_width, self.seam,
		                              ((-self.half_width, self.profile[0][1]), (self.half_width, self.profile[0][1])), (),
		                              lambda x, y: (x, y, self.half_depth), (0.0, 0.0, 1.0))
		self.back_face = OpeningFace(-self.half_width, self.half_width, self.seam,
		                             ((-self.half_width, self.profile[-1][1]), (self.half_width, self.profile[-1][1])),
		                             layout.rear_openings, lambda x, y: (x, y, -self.half_depth), (0.0, 0.0, -1.0))
		self.left_face = OpeningFace(-self.half_depth, self.half_depth, self.seam, self.profile, (),
		                             lambda z, y: (-self.half_width, y, z), (-1.0, 0.0, 0.0))
		self.right_face = OpeningFace(-self.half_depth, self.half_depth, self.seam, self.profile, layout.right_openings,
		                              lambda z, y: (self.half_width, y, z), (1.0, 0.0, 0.0))
		self.badge_lift = 0.01
		self.badge_left_share = 0.054
		self.badge_width_share = 0.27
		self.badge_centre_share_from_back = 0.385
		self.groove_count = 6
		self.groove_width = 0.07
		self.groove_rgb = (96, 92, 82)
		self.grill_margin_share = 0.008
		self.grill_gap_share = 0.006
		self.power_led_share_from_left = 0.905
		self.power_led_radius = 0.25
		self.power_led_segments = 24
		self.power_led_rgb = (120, 22, 16)
		self.power_label_text = "POWER"
		self.power_label_letters_width = 1.29
		self.power_label_font_px = 96
		self.power_label_aspect = 1.0
		self.power_label_gap = 0.15
		self.power_label_ink = (70, 66, 58)
		self._power_label_texture = None
		self._badge_texture = None
		self._badge_aspect = 1.0
		self._display_list = None

	def _holes_in_face_frame(self):
		origin_x, _, origin_z = self.keyboard_origin
		margin = self.hole_margin
		return tuple((x0 + origin_x - margin, x1 + origin_x + margin, z0 + origin_z - margin, z1 + origin_z + margin)
		             for x0, x1, z0, z1 in self.keyboard.key_areas())

	def enter_keyboard_face_frame(self):
		slope_front_z, slope_front_y = self.slope_origin
		glTranslatef(0.0, slope_front_y, slope_front_z)
		glRotatef(self.slope_degrees, 1.0, 0.0, 0.0)

	def enter_keyboard_frame(self):
		self.enter_keyboard_face_frame()
		glTranslatef(*self.keyboard_origin)

	def build(self):
		badge_picture = pygame.image.load(self.layout.badge_picture_path)
		self._badge_aspect = badge_picture.get_width() / badge_picture.get_height()
		self._badge_texture = upload_texture(badge_picture)
		self._power_label_texture = upload_texture(self._power_label_letters())
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_shell()
		glPushMatrix()
		self.enter_keyboard_face_frame()
		self.keyboard_face.draw(self.layout.case_rgb, self.hole_wall_shade)
		glPopMatrix()
		glEndList()

	def _draw_shell(self):
		case_rgb = self.layout.case_rgb
		self.front_face.draw(case_rgb)
		self.back_face.draw(case_rgb)
		self.left_face.draw(case_rgb)
		self.right_face.draw(case_rgb)
		self.back_face.draw_tunnels((0.0, 0.0, 1.0), self.wall, case_rgb, self.tunnel_shade)
		self.right_face.draw_tunnels((-1.0, 0.0, 0.0), self.wall, case_rgb, self.tunnel_shade)
		skipped_edges = (self.layout.keyboard_slope_edge, self.layout.badge_strip_edge)
		color(case_rgb)
		glBegin(GL_QUADS)
		for index, ((z0, y0), (z1, y1)) in enumerate(zip(self.profile, self.profile[1:])):
			if index not in skipped_edges:
				quad((-self.half_width, y0, z0), (self.half_width, y0, z0), (self.half_width, y1, z1),
				     (-self.half_width, y1, z1))
		glEnd()
		self._draw_badge_strip()

	def _strip_point(self, share_from_left, share_from_back, lift):
		front_z, front_y = self.profile[self.layout.badge_strip_edge]
		back_z, back_y = self.profile[self.layout.badge_strip_edge + 1]
		return (-self.half_width + 2 * self.half_width * share_from_left,
		        back_y + (front_y - back_y) * share_from_back + lift,
		        back_z + (front_z - back_z) * share_from_back)

	def _strip_depth(self):
		front_z, front_y = self.profile[self.layout.badge_strip_edge]
		back_z, back_y = self.profile[self.layout.badge_strip_edge + 1]
		return math.hypot(front_z - back_z, back_y - front_y)

	def _badge_depth_share(self):
		badge_width = 2 * self.half_width * self.badge_width_share
		return badge_width / self._badge_aspect / self._strip_depth()

	def _badge_back_and_front_shares(self):
		half_depth_share = self._badge_depth_share() / 2
		return self.badge_centre_share_from_back - half_depth_share, self.badge_centre_share_from_back + half_depth_share

	def _strip_quad(self, left_share, right_share, back_share, front_share, lift):
		for share_from_left, share_from_back in ((left_share, front_share), (right_share, front_share),
		                                         (right_share, back_share), (left_share, back_share)):
			glVertex3f(*self._strip_point(share_from_left, share_from_back, lift))

	def _draw_badge_strip(self):
		color(self.layout.case_rgb)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		self._strip_quad(0.0, 1.0, 0.0, 1.0, 0.0)
		glEnd()
		self._draw_grill()
		self._draw_power_led()
		self._draw_power_label()
		self._draw_badge()

	def _draw_grill(self):
		back_share, front_share = self._badge_back_and_front_shares()
		groove_depth_share = self.groove_width / self._strip_depth()
		badge_right_share = self.badge_left_share + self.badge_width_share
		label_left_share, _ = self._power_label_shares()
		led_left_share = label_left_share - self.grill_gap_share
		led_right_share = (self.power_led_share_from_left + self.power_led_radius / (2 * self.half_width)
		                   + self.grill_gap_share)
		spans = ((self.grill_margin_share, self.badge_left_share - self.grill_gap_share),
		         (badge_right_share + self.grill_gap_share, led_left_share),
		         (led_right_share, 1.0 - self.grill_margin_share))
		color(self.groove_rgb)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for groove_index in range(self.groove_count):
			groove_centre = back_share + (front_share - back_share) * (groove_index + 0.5) / self.groove_count
			for left_share, right_share in spans:
				self._strip_quad(left_share, right_share, groove_centre - groove_depth_share / 2,
				                 groove_centre + groove_depth_share / 2, self.badge_lift)
		glEnd()

	def _draw_power_led(self):
		centre_x, centre_y, centre_z = self._strip_point(self.power_led_share_from_left,
		                                                 self.badge_centre_share_from_back, self.badge_lift)
		color(self.power_led_rgb)
		glBegin(GL_TRIANGLE_FAN)
		glNormal3f(0.0, 1.0, 0.0)
		glVertex3f(centre_x, centre_y, centre_z)
		for segment in range(self.power_led_segments + 1):
			angle = 2 * math.pi * segment / self.power_led_segments
			glVertex3f(centre_x + self.power_led_radius * math.cos(angle), centre_y,
			           centre_z + self.power_led_radius * math.sin(angle))
		glEnd()

	def _power_label_letters(self):
		pygame.font.init()
		rendered = pygame.font.SysFont("arial", self.power_label_font_px, bold=True).render(
			self.power_label_text, True, self.power_label_ink)
		letters = rendered.subsurface(rendered.get_bounding_rect()).copy()
		self.power_label_aspect = letters.get_width() / letters.get_height()
		return letters

	def _power_label_shares(self):
		strip_width = 2 * self.half_width
		right_share = (self.power_led_share_from_left
		               - (self.power_led_radius + self.power_label_gap) / strip_width)
		return right_share - self.power_label_letters_width / strip_width, right_share

	def _draw_power_label(self):
		left_share, right_share = self._power_label_shares()
		half_depth_share = self.power_label_letters_width / self.power_label_aspect / self._strip_depth() / 2
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		self._draw_strip_texture(self._power_label_texture, left_share, right_share,
		                         self.badge_centre_share_from_back - half_depth_share,
		                         self.badge_centre_share_from_back + half_depth_share)
		glDisable(GL_BLEND)

	def _draw_badge(self):
		back_share, front_share = self._badge_back_and_front_shares()
		self._draw_strip_texture(self._badge_texture, self.badge_left_share,
		                         self.badge_left_share + self.badge_width_share, back_share, front_share)

	def _draw_strip_texture(self, texture, left_share, right_share, back_share, front_share):
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, texture)
		glColor3f(1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for (texture_s, texture_t), (share_from_left, share_from_back) in (
				((0.0, 0.0), (left_share, front_share)), ((1.0, 0.0), (right_share, front_share)),
				((1.0, 1.0), (right_share, back_share)), ((0.0, 1.0), (left_share, back_share))):
			glTexCoord2f(texture_s, texture_t)
			glVertex3f(*self._strip_point(share_from_left, share_from_back, 2 * self.badge_lift))
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def draw(self):
		glCallList(self._display_list)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)
			glDeleteTextures([self._badge_texture, self._power_label_texture])
			self._display_list = None
