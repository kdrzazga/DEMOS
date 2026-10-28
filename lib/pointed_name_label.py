import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluProject


class OutlinedTextTexture:

	def __init__(self, text, font_pixel_size, text_color=(255, 255, 255), envelope_color=(0, 0, 0),
	             envelope_pixel_width=2, font_name="arial"):
		self.text = text
		pygame.font.init()
		font = pygame.font.SysFont(font_name, font_pixel_size, bold=True)
		surface = self._render_text_inside_envelope(font, text, text_color, envelope_color, envelope_pixel_width)
		self.pixel_width, self.pixel_height = surface.get_size()
		self.texture_id = self._upload_surface_as_texture(surface)

	@staticmethod
	def _render_text_inside_envelope(font, text, text_color, envelope_color, envelope_pixel_width):
		text_surface = font.render(text, True, text_color)
		envelope_surface = font.render(text, True, envelope_color)
		width, height = text_surface.get_size()
		combined_surface = pygame.Surface((width + 2 * envelope_pixel_width, height + 2 * envelope_pixel_width),
		                                  pygame.SRCALPHA)
		for offset_x in range(-envelope_pixel_width, envelope_pixel_width + 1):
			for offset_y in range(-envelope_pixel_width, envelope_pixel_width + 1):
				if offset_x * offset_x + offset_y * offset_y <= envelope_pixel_width * envelope_pixel_width:
					combined_surface.blit(envelope_surface,
					                      (envelope_pixel_width + offset_x, envelope_pixel_width + offset_y))
		combined_surface.blit(text_surface, (envelope_pixel_width, envelope_pixel_width))
		return combined_surface

	@staticmethod
	def _upload_surface_as_texture(surface):
		width, height = surface.get_size()
		rgba_bytes_top_row_first = pygame.image.tobytes(surface, "RGBA", False)
		texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             rgba_bytes_top_row_first)
		return texture_id

	def draw_with_top_left_at(self, left_x, top_y, opacity):
		left_x, top_y = round(left_x), round(top_y)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glColor4f(1.0, 1.0, 1.0, opacity)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0)
		glVertex2f(left_x, top_y)
		glTexCoord2f(1.0, 0.0)
		glVertex2f(left_x + self.pixel_width, top_y)
		glTexCoord2f(1.0, 1.0)
		glVertex2f(left_x + self.pixel_width, top_y + self.pixel_height)
		glTexCoord2f(0.0, 1.0)
		glVertex2f(left_x, top_y + self.pixel_height)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		glDeleteTextures([self.texture_id])


class PointedNameLabel:

	def __init__(self, name, screen_scale=1.0, font_pixel_size=22, pointer_offset_pixels=(120.0, -95.0),
	             line_core_pixel_width=2.0, line_envelope_pixel_width=1.0, line_core_color=(0.0, 0.0, 0.0),
	             line_envelope_color=(1.0, 1.0, 1.0), gap_between_line_end_and_text_pixels=5.0,
	             line_growing_seconds=0.25):
		self.name = name
		self.screen_scale = screen_scale
		self.pointer_offset_pixels = (pointer_offset_pixels[0] * screen_scale, pointer_offset_pixels[1] * screen_scale)
		self.line_core_pixel_width = line_core_pixel_width
		self.line_envelope_pixel_width = line_envelope_pixel_width
		self.line_core_color = line_core_color
		self.line_envelope_color = line_envelope_color
		self.gap_between_line_end_and_text_pixels = gap_between_line_end_and_text_pixels * screen_scale
		self.line_growing_seconds = line_growing_seconds
		self.name_texture = OutlinedTextTexture(name, max(10, round(font_pixel_size * screen_scale)))

	def draw(self, pointed_screen_x, pointed_screen_y, label_goes_to_the_right, seconds_since_appearing, opacity):
		horizontal_direction = 1.0 if label_goes_to_the_right else -1.0
		line_growth = min(1.0, seconds_since_appearing / self.line_growing_seconds)
		line_end_x = pointed_screen_x + horizontal_direction * self.pointer_offset_pixels[0] * line_growth
		line_end_y = pointed_screen_y + self.pointer_offset_pixels[1] * line_growth
		self._draw_enveloped_line(pointed_screen_x, pointed_screen_y, line_end_x, line_end_y, opacity)
		if line_growth >= 1.0:
			self._draw_name_beside_line_end(line_end_x, line_end_y, horizontal_direction, opacity)

	def _draw_enveloped_line(self, start_x, start_y, end_x, end_y, opacity):
		envelope_width = self.line_core_pixel_width + 2 * self.line_envelope_pixel_width
		for line_width, line_color in ((envelope_width, self.line_envelope_color),
		                               (self.line_core_pixel_width, self.line_core_color)):
			glLineWidth(line_width)
			glPointSize(line_width)
			glColor4f(*line_color, opacity)
			glBegin(GL_LINES)
			glVertex2f(start_x, start_y)
			glVertex2f(end_x, end_y)
			glEnd()
			glBegin(GL_POINTS)
			glVertex2f(start_x, start_y)
			glVertex2f(end_x, end_y)
			glEnd()

	def _draw_name_beside_line_end(self, line_end_x, line_end_y, horizontal_direction, opacity):
		if horizontal_direction > 0:
			text_left_x = line_end_x + self.gap_between_line_end_and_text_pixels
		else:
			text_left_x = line_end_x - self.gap_between_line_end_and_text_pixels - self.name_texture.pixel_width
		text_top_y = line_end_y - self.name_texture.pixel_height / 2
		self.name_texture.draw_with_top_left_at(text_left_x, text_top_y, opacity)

	def destroy(self):
		self.name_texture.destroy()


class ScreenSpaceProjector:

	def __init__(self):
		self.modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self.projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
		self.viewport = glGetIntegerv(GL_VIEWPORT)

	@property
	def viewport_width(self):
		return int(self.viewport[2])

	@property
	def viewport_height(self):
		return int(self.viewport[3])

	def screen_position_from_top_left(self, x, y, z):
		window_x, window_y, _ = gluProject(x, y, z, self.modelview_matrix, self.projection_matrix, self.viewport)
		return window_x - self.viewport[0], self.viewport_height - (window_y - self.viewport[1])

	def begin_pixel_overlay(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT | GL_POINT_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_LINE_SMOOTH)
		glDisable(GL_POINT_SMOOTH)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0, self.viewport_width, self.viewport_height, 0, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()

	@staticmethod
	def end_pixel_overlay():
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopAttrib()
