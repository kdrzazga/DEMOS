from OpenGL.GL import *

from lib.pointed_name_label import OutlinedTextTexture, ScreenSpaceProjector
from demos.forty_five.font import FONT_PATH


class ChipNameFlash:

	def __init__(self, chip_animation, name):
		self.chip_animation = chip_animation
		self.name = name
		self.flash_count = 3
		self.flash_seconds = 0.3
		self.pause_seconds_between_flashes = 0.15
		self.font_pixel_size = 56
		self.design_screen_height = 800.0
		self.gap_above_chip_pixels = 12.0
		self.text_rgb = (255, 255, 255)
		self.envelope_rgb = (0, 0, 0)
		self.elapsed_seconds = None
		self._text_texture = None

	def build(self):
		screen_scale = glGetIntegerv(GL_VIEWPORT)[3] / self.design_screen_height
		self._text_texture = OutlinedTextTexture(self.name, round(self.font_pixel_size * screen_scale),
		                                         text_color=self.text_rgb, envelope_color=self.envelope_rgb,
		                                         font_path=FONT_PATH)

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def _seconds_from_flash_to_flash(self):
		return self.flash_seconds + self.pause_seconds_between_flashes

	@property
	def duration_seconds(self):
		return self._seconds_from_flash_to_flash * self.flash_count

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.duration_seconds

	def reset(self):
		self.elapsed_seconds = None

	def start(self):
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def _is_lit(self):
		if not self.started or self.finished:
			return False
		return self.elapsed_seconds % self._seconds_from_flash_to_flash < self.flash_seconds

	def draw(self):
		if not self._is_lit():
			return
		projector = ScreenSpaceProjector()
		pose = self.chip_animation.pose
		_, chip_height_fraction = self.chip_animation.screen_size_fractions(pose)
		centre_x = pose.fraction_from_left * projector.viewport_width
		chip_top_y = (pose.fraction_from_top - chip_height_fraction / 2) * projector.viewport_height
		chip_bottom_y = (pose.fraction_from_top + chip_height_fraction / 2) * projector.viewport_height
		gap_pixels = self.gap_above_chip_pixels * projector.viewport_height / self.design_screen_height
		text_top_y = chip_top_y - gap_pixels - self._text_texture.pixel_height
		if text_top_y < 0.0:
			text_top_y = chip_bottom_y + gap_pixels
		projector.begin_pixel_overlay()
		self._text_texture.draw_with_top_left_at(centre_x - self._text_texture.pixel_width / 2, text_top_y, 1.0)
		projector.end_pixel_overlay()

	def destroy(self):
		if self._text_texture:
			self._text_texture.destroy()
			self._text_texture = None
