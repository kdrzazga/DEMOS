from OpenGL.GL import *

from demos.forty_five.font import FONT_PATH
from lib.caption_sequence import CaptionSequence


class YearFlashFactory:

	def __init__(self):
		self.flash_count = 3
		self.flash_seconds = 0.5
		self.pause_seconds_between_flashes = 0.25
		self.color = (230, 40, 40)
		self.font_pixel_size = 110
		self.left_margin_pixels = 170.0
		self.design_screen_height = 800.0
		self.gap_below_chips_pixels = 30.0

	def _screen_scale(self):
		return glGetIntegerv(GL_VIEWPORT)[3] / self.design_screen_height

	def _top_margin_pixels_below(self, chips_bottom_fraction_from_top):
		return chips_bottom_fraction_from_top * self.design_screen_height + self.gap_below_chips_pixels

	def create_below_fraction(self, year, chips_bottom_fraction_from_top):
		return CaptionSequence(
			(year,) * self.flash_count, seconds_per_caption=self.flash_seconds,
			pause_seconds_between_captions=self.pause_seconds_between_flashes, text_color=self.color,
			screen_scale=self._screen_scale(), font_pixel_size=self.font_pixel_size,
			margin_from_top_left_pixels=(self.left_margin_pixels,
			                             self._top_margin_pixels_below(chips_bottom_fraction_from_top)),
			font_path=FONT_PATH)

	def create_flashing_below(self, year, chip_animations):
		lowest_chip_bottom_fraction = max(chip_animation.bottom_center_screen_fractions()[1]
		                                  for chip_animation in chip_animations)
		year_flashes = self.create_below_fraction(year, lowest_chip_bottom_fraction)
		year_flashes.start()
		return year_flashes

	def move_below_fraction(self, year_flashes, chips_bottom_fraction_from_top):
		screen_scale = self._screen_scale()
		year_flashes.margin_from_top_left_pixels = (
			self.left_margin_pixels * screen_scale,
			self._top_margin_pixels_below(chips_bottom_fraction_from_top) * screen_scale)
