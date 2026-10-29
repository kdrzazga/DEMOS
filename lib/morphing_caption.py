import pygame
from OpenGL.GL import *

from lib.laser_line import PictureTexture
from lib.typer import FONT_PATH


class MorphingCaptionSegment:

	def __init__(self, outgoing_text, incoming_text, font, text_color):
		self.outgoing_texture = PictureTexture(font.render(outgoing_text, False, text_color))
		self.stays_unchanged = outgoing_text == incoming_text
		self.incoming_texture = self.outgoing_texture if self.stays_unchanged else PictureTexture(
			font.render(incoming_text, False, text_color))

	def width_at(self, text_height, morph_progress):
		outgoing_width = text_height * self.outgoing_texture.aspect_ratio
		incoming_width = text_height * self.incoming_texture.aspect_ratio
		return outgoing_width + (incoming_width - outgoing_width) * morph_progress

	def draw_with_left_edge_at(self, left_x, text_height, morph_progress):
		if self.stays_unchanged:
			self._draw_texture(self.outgoing_texture, left_x, text_height, 1.0)
			return
		self._draw_texture(self.outgoing_texture, left_x, text_height, 1.0 - morph_progress)
		self._draw_texture(self.incoming_texture, left_x, text_height, morph_progress)

	@staticmethod
	def _draw_texture(texture, left_x, text_height, opacity):
		if opacity <= 0.0:
			return
		texture_width = text_height * texture.aspect_ratio
		glPushMatrix()
		glTranslatef(left_x + texture_width / 2, 0.0, 0.0)
		glColor4f(1.0, 1.0, 1.0, opacity)
		texture.draw_vertical_strip(0.0, 1.0, texture_width, text_height)
		glPopMatrix()

	def destroy(self):
		self.outgoing_texture.destroy()
		if not self.stays_unchanged:
			self.incoming_texture.destroy()


class MorphingCaption:

	def __init__(self, outgoing_and_incoming_segment_texts, text_height, font_path=FONT_PATH, font_pixel_size=48,
	             text_color=(255, 255, 255)):
		self.text_height = text_height
		pygame.font.init()
		font = pygame.font.Font(font_path, font_pixel_size)
		self.segments = [MorphingCaptionSegment(outgoing_text, incoming_text, font, text_color)
		                 for outgoing_text, incoming_text in outgoing_and_incoming_segment_texts]

	def width_at(self, morph_progress):
		return sum(segment.width_at(self.text_height, morph_progress) for segment in self.segments)

	def draw_centered_at(self, center_x, center_y, depth_z, morph_progress):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(center_x, center_y, depth_z)
		segment_left_x = -self.width_at(morph_progress) / 2
		for segment in self.segments:
			segment.draw_with_left_edge_at(segment_left_x, self.text_height, morph_progress)
			segment_left_x += segment.width_at(self.text_height, morph_progress)
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		for segment in self.segments:
			segment.destroy()
		self.segments = []
