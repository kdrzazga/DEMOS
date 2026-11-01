import pygame
from OpenGL.GL import *

from demos.forty_five.c64breadbox.breadbin_layout import OpeningRect
from demos.forty_five.c64breadbox.opening_face import OpeningFace
from demos.forty_five.geometry import color, upload_texture


class BreadbinWall:

	def __init__(self, outer_face, inner_face, rim_face, inward):
		self.outer_face = outer_face
		self.inner_face = inner_face
		self.rim_face = rim_face
		self.inward = inward


class BreadbinBase:

	def __init__(self, layout):
		self.layout = layout
		self.half_width = layout.width_cm / 2
		self.half_depth = layout.depth_cm / 2
		self.wall = layout.wall_thickness_cm
		self.seam = layout.seam_height_cm
		self.floor = layout.floor_thickness_cm
		self.inner_shade = 0.82
		self.tunnel_shade = 0.6
		self.walls = (
			self._wall_along_x(self.half_depth, 1.0, ()),
			self._wall_along_x(-self.half_depth, -1.0, layout.rear_openings),
			self._wall_along_z(-self.half_width, -1.0, ()),
			self._wall_along_z(self.half_width, 1.0, layout.right_openings),
		)
		self._bottom_texture = None
		self._bottom_photo_size = None
		self._display_list = None

	def _rim_openings(self, openings):
		return tuple(OpeningRect(opening.start, opening.end, -1.0, self.wall + 1.0)
		             for opening in openings if opening.top > self.seam)

	def _wall_along_x(self, outer_z, outward, openings):
		inner_z = outer_z - outward * self.wall
		inner_half_width = self.half_width - self.wall
		seam = self.seam
		return BreadbinWall(
			OpeningFace(-self.half_width, self.half_width, 0.0, ((-self.half_width, seam), (self.half_width, seam)),
			            openings, lambda x, y: (x, y, outer_z), (0.0, 0.0, outward)),
			OpeningFace(-inner_half_width, inner_half_width, self.floor,
			            ((-inner_half_width, seam), (inner_half_width, seam)),
			            openings, lambda x, y: (x, y, inner_z), (0.0, 0.0, -outward)),
			OpeningFace(-self.half_width, self.half_width, 0.0, ((-self.half_width, self.wall), (self.half_width, self.wall)),
			            self._rim_openings(openings), lambda x, inset: (x, seam, outer_z - outward * inset),
			            (0.0, 1.0, 0.0)),
			(0.0, 0.0, -outward))

	def _wall_along_z(self, outer_x, outward, openings):
		inner_x = outer_x - outward * self.wall
		inner_half_depth = self.half_depth - self.wall
		seam = self.seam
		return BreadbinWall(
			OpeningFace(-self.half_depth, self.half_depth, 0.0, ((-self.half_depth, seam), (self.half_depth, seam)),
			            openings, lambda z, y: (outer_x, y, z), (outward, 0.0, 0.0)),
			OpeningFace(-inner_half_depth, inner_half_depth, self.floor,
			            ((-inner_half_depth, seam), (inner_half_depth, seam)),
			            openings, lambda z, y: (inner_x, y, z), (-outward, 0.0, 0.0)),
			OpeningFace(-self.half_depth, self.half_depth, 0.0, ((-self.half_depth, self.wall), (self.half_depth, self.wall)),
			            self._rim_openings(openings), lambda z, inset: (outer_x - outward * inset, seam, z),
			            (0.0, 1.0, 0.0)),
			(-outward, 0.0, 0.0))

	def build(self):
		surface = pygame.image.load(self.layout.bottom_photo_path)
		self._bottom_photo_size = surface.get_size()
		self._bottom_texture = upload_texture(surface)
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_walls()
		self._draw_inner_floor()
		self._draw_bottom()
		glEndList()

	def _draw_walls(self):
		case_rgb = self.layout.case_rgb
		for wall in self.walls:
			wall.outer_face.draw(case_rgb)
			wall.inner_face.draw(case_rgb, self.inner_shade)
			wall.rim_face.draw(case_rgb)
			wall.outer_face.draw_tunnels(wall.inward, self.wall, case_rgb, self.tunnel_shade)

	def _draw_inner_floor(self):
		inner_half_width = self.half_width - self.wall
		inner_half_depth = self.half_depth - self.wall
		color(self.layout.case_rgb, self.inner_shade)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for x, z in ((-inner_half_width, inner_half_depth), (inner_half_width, inner_half_depth),
		             (inner_half_width, -inner_half_depth), (-inner_half_width, -inner_half_depth)):
			glVertex3f(x, self.floor, z)
		glEnd()

	def _bottom_texture_coordinate(self, x, z):
		crop = self.layout.bottom_photo_crop
		photo_width, photo_height = self._bottom_photo_size
		photo_x = crop.left + (self.half_width - x) / (2 * self.half_width) * (crop.right - crop.left)
		photo_y = crop.top + (z + self.half_depth) / (2 * self.half_depth) * (crop.bottom - crop.top)
		return photo_x / photo_width, 1.0 - photo_y / photo_height

	def _draw_bottom(self):
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._bottom_texture)
		glColor3f(1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glNormal3f(0.0, -1.0, 0.0)
		for x, z in ((-self.half_width, -self.half_depth), (self.half_width, -self.half_depth),
		             (self.half_width, self.half_depth), (-self.half_width, self.half_depth)):
			glTexCoord2f(*self._bottom_texture_coordinate(x, z))
			glVertex3f(x, 0.0, z)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def draw(self):
		glCallList(self._display_list)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)
			glDeleteTextures([self._bottom_texture])
			self._display_list = None
