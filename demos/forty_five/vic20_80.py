import os

import pygame

from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface
from demos.forty_five.chip_listing import ChipListing

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
VIC20_IMAGE_PATH = os.path.join(os.path.dirname(FORTY_FIVE_DIRECTORY), "common", "commodore", "vic20.png")
VIC20_SOUND_PATH = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=", "80VIC-20.mp3")
VIC20_CHIPS_HEADER = "Chips used in VIC-20:"
VIC20_CHIP_NAMES = ("Processor 6502", "VIA", "BASIC ROM", "Character ROM", "VIC")


class Vic20Arrival:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.wait_seconds = 2.0
		self.vic20_height_in_screen_heights = 0.4
		self.vic20_enter_seconds = 3.0
		self.vic20_swing_amplitude_degrees = 12.0
		self.vic20_picture = PictureTexture.load(VIC20_IMAGE_PATH)
		self.vic20 = PictureSurface(self.vic20_picture, screen_plane, self.vic20_height_in_screen_heights,
		                            swing_amplitude_degrees=self.vic20_swing_amplitude_degrees)
		self.vic20_sound = self._load_sound(VIC20_SOUND_PATH)
		self.chip_listing = ChipListing(screen_plane, VIC20_CHIPS_HEADER, VIC20_CHIP_NAMES, self.vic20,
		                                ((0.3, 0.1), (0.4, 0.1), (0.5, 0.1), (0.6, 0.1), (0.7, 0.1)))
		self.chip_listing_margin_in_screen_heights = 0.04
		self.chip_listing_raise_in_lines = 2
		self.chip_listing.place_in_bottom_right_corner(self.chip_listing_margin_in_screen_heights
		                                               * screen_plane.visible_height)
		self.chip_listing.raise_by_lines(self.chip_listing_raise_in_lines)
		self.listing_hold_seconds = 2.0
		self.vic20_drop_seconds = 1.5
		self.vic20_drop_start_y = None
		self.phase = "idle"
		self.phase_seconds = 0.0

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	def begin(self):
		self._enter("wait")

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	@property
	def vic20_visible(self):
		return self.phase not in ("idle", "wait")

	@property
	def playback_finished(self):
		return self.phase in ("arrived", "typing", "hold", "vic20_drops", "done")

	@property
	def done(self):
		return self.phase == "done"

	def list_chips(self, chip_animations):
		self.chip_listing.begin(chip_animations)
		self._enter("typing")

	def update(self, seconds):
		self.phase_seconds += seconds
		self.vic20.update(seconds)
		if self.phase == "wait" and self.phase_seconds >= self.wait_seconds:
			self._start_vic20_arrival()
		elif self.phase == "vic20_arrives" and self.phase_seconds >= self.vic20_sound.get_length():
			self._enter("arrived")
		elif self.phase == "typing":
			self.chip_listing.update(seconds)
			if self.chip_listing.finished:
				self._enter("hold")
		elif self.phase == "hold" and self.phase_seconds >= self.listing_hold_seconds:
			self._drop_vic20()
		elif self.phase == "vic20_drops":
			self.chip_listing.update(seconds)
			self.chip_listing.fade_lines(max(0.0, 1.0 - self.phase_seconds / self.vic20_drop_seconds))
			self.chip_listing.vertical_offset = self.vic20.world_center_point[1] - self.vic20_drop_start_y
			if self.phase_seconds >= self.vic20_drop_seconds:
				self._enter("done")

	def _drop_vic20(self):
		self._enter("vic20_drops")
		center_x, self.vic20_drop_start_y = self.vic20.world_center_point
		screen_bottom_y = -self.screen_plane.visible_height / 2
		vic20_drop_distance = self.vic20_drop_start_y + self.vic20.picture_height / 2 - screen_bottom_y
		listing_drop_distance = self.chip_listing.top_y - screen_bottom_y
		drop_distance = max(vic20_drop_distance, listing_drop_distance)
		self.vic20.glide_center_to(
			self.screen_plane.screen_fractions_from_world_point(center_x, self.vic20_drop_start_y - drop_distance),
			self.vic20_drop_seconds, easing=ease_in_cubic)

	def _start_vic20_arrival(self):
		self._enter("vic20_arrives")
		self.vic20_sound.play()
		_, vic20_fraction_from_top = self.vic20.center_fractions_with_bottom_edge_on_screen_bottom(0.0)
		self.vic20.place_center_at(self.vic20.center_fractions_just_beyond_left_edge(vic20_fraction_from_top))
		self.vic20.glide_center_to(self.vic20.center_fractions_with_left_edge_on_screen_left(vic20_fraction_from_top),
		                           self.vic20_enter_seconds, easing=ease_out_cubic)

	def draw(self):
		if self.vic20_visible:
			self.vic20.draw()

	def draw_overlay(self):
		if self.phase in ("typing", "hold", "vic20_drops"):
			self.chip_listing.draw()

	def destroy(self):
		self.vic20_sound.stop()
		self.vic20_picture.destroy()
		self.chip_listing.destroy()
