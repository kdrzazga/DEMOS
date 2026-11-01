import pygame
from OpenGL.GL import *

from demos.forty_five.geometry import upload_texture
from lib.typer import FONT_PATH


class NameCaption:

	def __init__(self, lines):
		self.lines = lines
		self.font_px = 64
		self.font_rgb = (255, 255, 255)
		self._texture = None

	def build(self):
		pygame.font.init()
		font = pygame.font.Font(FONT_PATH, self.font_px)
		line_height_px = font.get_linesize()
		width_px = max(font.size(line)[0] for line in self.lines)
		surface = pygame.Surface((width_px, line_height_px * len(self.lines)), pygame.SRCALPHA)
		for index, line in enumerate(self.lines):
			line_surface = font.render(line, True, self.font_rgb)
			surface.blit(line_surface, ((width_px - line_surface.get_width()) // 2, index * line_height_px))
		self.aspect = surface.get_width() / surface.get_height()
		self._texture = upload_texture(surface)

	def draw_below(self, centre_x, top_y, depth, line_height):
		height = line_height * len(self.lines)
		half_width = height * self.aspect / 2
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._texture)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		for (s, t), (across, y) in (((0, 0), (-1, top_y - height)), ((1, 0), (1, top_y - height)),
		                            ((1, 1), (1, top_y)), ((0, 1), (-1, top_y))):
			glTexCoord2f(s, t)
			glVertex3f(centre_x + across * half_width, y, depth)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		if self._texture:
			glDeleteTextures([self._texture])
			self._texture = None
