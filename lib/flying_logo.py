import math

import pygame
from OpenGL.GL import *

from lib.laser_line import PictureTexture, smooth_step
from lib.typer import FONT_PATH


def ease_out_cubic(progress):
	return 1.0 - (1.0 - progress) ** 3


def ease_in_cubic(progress):
	return progress ** 3


def render_centered_text_lines(text_lines, font_path, font_pixel_size, text_color, line_spacing_fraction=0.35):
	pygame.font.init()
	font = pygame.font.Font(font_path, font_pixel_size)
	rendered_lines = [font.render(text_line, False, text_color) for text_line in text_lines]
	line_step = round(font.get_linesize() * (1.0 + line_spacing_fraction))
	surface_width = max(rendered_line.get_width() for rendered_line in rendered_lines)
	surface_height = line_step * (len(rendered_lines) - 1) + rendered_lines[-1].get_height()
	surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
	for line_index, rendered_line in enumerate(rendered_lines):
		surface.blit(rendered_line, ((surface_width - rendered_line.get_width()) // 2, line_index * line_step))
	return surface


class FlyingLogo:

	def __init__(self, image_path, aspect_ratio, field_of_view_degrees, camera_distance, flight_seconds=6.5,
	             settle_time=1.5, logo_height=2.0, scale_at_screen_edges=0.7, scale_when_settled=2.2, full_turns=1,
	             offscreen_margin=1.0, settled_caption_lines=(), caption_font_path=FONT_PATH,
	             caption_color=(255, 255, 255), caption_font_pixel_size=48, caption_width_in_logo_widths=1.4,
	             caption_gap_below_logo_in_logo_heights=0.2, caption_fade_in_seconds=0.4):
		self.camera_distance = camera_distance
		self.flight_seconds = flight_seconds
		self.settle_time = settle_time
		self.arrival_seconds = flight_seconds / 2
		self.departure_seconds = self.arrival_seconds
		self.logo_height = logo_height
		self.scale_at_screen_edges = scale_at_screen_edges
		self.scale_when_settled = scale_when_settled
		self.full_turns = full_turns
		self.caption_gap_below_logo_in_logo_heights = caption_gap_below_logo_in_logo_heights
		self.caption_fade_in_seconds = caption_fade_in_seconds
		self.picture = PictureTexture.load(image_path)
		self.logo_width = logo_height * self.picture.aspect_ratio
		self.caption_picture = None
		if settled_caption_lines:
			self.caption_picture = PictureTexture(render_centered_text_lines(
				settled_caption_lines, caption_font_path, caption_font_pixel_size, caption_color))
			self.caption_width = self.logo_width * caption_width_in_logo_widths
			self.caption_height = self.caption_width / self.caption_picture.aspect_ratio
		visible_half_width = camera_distance * math.tan(math.radians(field_of_view_degrees) / 2) * aspect_ratio
		self.offscreen_x = visible_half_width + self.logo_width * scale_at_screen_edges / 2 + offscreen_margin
		self.restart()

	def restart(self):
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def total_seconds(self):
		return self.flight_seconds + self.settle_time

	@property
	def finished(self):
		return self.elapsed_seconds >= self.total_seconds

	@property
	def arrival_progress(self):
		return min(1.0, self.elapsed_seconds / self.arrival_seconds)

	@property
	def departure_progress(self):
		departure_start_second = self.arrival_seconds + self.settle_time
		return max(0.0, min(1.0, (self.elapsed_seconds - departure_start_second) / self.departure_seconds))

	@property
	def is_settled(self):
		return self.arrival_seconds <= self.elapsed_seconds < self.arrival_seconds + self.settle_time

	@property
	def caption_opacity(self):
		if not self.is_settled:
			return 0.0
		seconds_since_settling = self.elapsed_seconds - self.arrival_seconds
		return max(0.0, min(1.0, seconds_since_settling / self.caption_fade_in_seconds))

	def _current_x(self):
		arrival_x = self.offscreen_x * (1.0 - ease_out_cubic(self.arrival_progress))
		departure_x = -self.offscreen_x * ease_in_cubic(self.departure_progress)
		return arrival_x + departure_x

	def _current_scale(self):
		scale_growth = self.scale_when_settled - self.scale_at_screen_edges
		zoom_amount = ease_out_cubic(self.arrival_progress) - ease_in_cubic(self.departure_progress)
		return self.scale_at_screen_edges + scale_growth * zoom_amount

	def _current_spin_degrees(self):
		return 360.0 * self.full_turns * smooth_step(self.arrival_progress)

	def draw(self):
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
		glTranslatef(self._current_x(), 0.0, -self.camera_distance)
		glRotatef(self._current_spin_degrees(), 0.0, 1.0, 0.0)
		current_scale = self._current_scale()
		glScalef(current_scale, current_scale, 1.0)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.picture.draw_vertical_strip(0.0, 1.0, self.logo_width, self.logo_height)
		self._draw_caption_below_logo()
		glPopMatrix()
		glPopAttrib()

	def _draw_caption_below_logo(self):
		caption_opacity = self.caption_opacity
		if self.caption_picture is None or caption_opacity <= 0.0:
			return
		caption_center_y = -(self.logo_height / 2 + self.logo_height * self.caption_gap_below_logo_in_logo_heights
		                     + self.caption_height / 2)
		glPushMatrix()
		glTranslatef(0.0, caption_center_y, 0.0)
		glColor4f(1.0, 1.0, 1.0, caption_opacity)
		self.caption_picture.draw_vertical_strip(0.0, 1.0, self.caption_width, self.caption_height)
		glPopMatrix()

	def destroy(self):
		self.picture.destroy()
		if self.caption_picture is not None:
			self.caption_picture.destroy()
