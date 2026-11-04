import pygame
from OpenGL.GL import *

from lib.geometry import upload_texture
from demos.forty_five.font import FONT_PATH


class PictureDescription:

	def __init__(self, lines):
		self.lines = lines
		self.font_px = 64
		self.font_rgb = (255, 255, 255)
		self._texture = None

	def build(self):
		pygame.font.init()
		font = pygame.font.Font(FONT_PATH, self.font_px)
		letter_top_px = font.get_ascent() - font.metrics("M")[0][3]
		room_below_letters_px = font.get_linesize() - letter_top_px - self.font_px
		width_px = max(font.size(line)[0] for line in self.lines)
		letters_height_px = self.font_px * len(self.lines)
		surface_height_px = letter_top_px + letters_height_px + room_below_letters_px
		surface = pygame.Surface((width_px, surface_height_px), pygame.SRCALPHA)
		for index, line in enumerate(self.lines):
			line_surface = font.render(line, True, self.font_rgb)
			surface.blit(line_surface, ((width_px - line_surface.get_width()) // 2, index * self.font_px))
		self.aspect = width_px / letters_height_px
		self.letter_top_fraction = letter_top_px / surface_height_px
		self.letters_fraction = letters_height_px / surface_height_px
		self._texture = upload_texture(surface)

	def draw_below(self, centre_x, top_y, depth, line_height):
		letters_height = line_height * len(self.lines)
		height = letters_height / self.letters_fraction
		quad_top_y = top_y + height * self.letter_top_fraction
		half_width = letters_height * self.aspect / 2
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._texture)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		for (s, t), (across, y) in (((0, 0), (-1, quad_top_y - height)), ((1, 0), (1, quad_top_y - height)),
		                            ((1, 1), (1, quad_top_y)), ((0, 1), (-1, quad_top_y))):
			glTexCoord2f(s, t)
			glVertex3f(centre_x + across * half_width, y, depth)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		if self._texture:
			glDeleteTextures([self._texture])
			self._texture = None
