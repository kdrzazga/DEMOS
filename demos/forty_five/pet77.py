import os

import pygame

from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface
from demos.forty_five.chip_listing import ChipListing

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PET_IMAGE_PATH = os.path.join(os.path.dirname(FORTY_FIVE_DIRECTORY), "common", "commodore", "pet.png")
PET_SOUND_PATH = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=", "77PET.mp3")
PET_CHIPS_HEADER = "Chips used in PET:"
PET_CHIP_NAMES = ("Processor 6502", "PIA", "VIA", "BASIC ROM", "Character ROM")


class PetIntroduction:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.wait_seconds = 1.0
		self.pet_height_in_screen_heights = 0.5
		self.pet_rest_fraction_from_left = 0.28
		self.pet_enter_seconds = 3.0
		self.pet_swing_amplitude_degrees = 12.0
		self.peddle_lower_seconds = 2.0
		self.rom_appear_seconds = 0.4
		self.rom_sway_seconds = 2.0
		self.rom_join_seconds = 2.0
		self.rom_fraction_from_top = 0.72
		self.clear_stage_seconds = 1.5
		self.final_hold_seconds = 2.0
		self.pet_drop_seconds = 1.5
		self.pet_drop_start_y = None
		self.pet_picture = PictureTexture.load(PET_IMAGE_PATH)
		self.pet = PictureSurface(self.pet_picture, screen_plane, self.pet_height_in_screen_heights,
		                          swing_amplitude_degrees=self.pet_swing_amplitude_degrees)
		self.pet_sound = self._load_sound(PET_SOUND_PATH)
		self.chip_listing = ChipListing(screen_plane, PET_CHIPS_HEADER, PET_CHIP_NAMES, self.pet,
		                                ((0.25, 0.05), (0.375, 0.05), (0.5, 0.05), (0.625, 0.05), (0.75, 0.05)))
		self.chip_listing_margin_in_screen_heights = 0.04
		self.chip_listing.place_in_bottom_right_corner(self.chip_listing_margin_in_screen_heights
		                                               * screen_plane.visible_height)
		self.chuck_peddle = None
		self.character_rom = None
		self.peddle_destroyed = False
		self.phase = "idle"
		self.phase_seconds = 0.0

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	def begin(self, chuck_peddle, processor, pia, via, basic_rom, character_rom):
		self.chuck_peddle = chuck_peddle
		self.basic_rom = basic_rom
		self.character_rom = character_rom
		self.peddle_destroyed = False
		self.chip_listing.begin((processor, pia, via, basic_rom, character_rom))
		self.pet_drop_start_y = None
		self._enter("wait")

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	@property
	def done(self):
		return self.phase == "done"

	@property
	def pet_visible(self):
		return self.phase not in ("idle", "wait")

	def update(self, seconds):
		self.phase_seconds += seconds
		self.pet.update(seconds)
		if self.phase in ("typing", "hold", "pet_drops"):
			self.chip_listing.update(seconds)
		if self.phase == "wait" and self.phase_seconds >= self.wait_seconds:
			self._start_pet_arrival()
		elif self.phase == "pet_arrives" and self.phase_seconds >= self.pet_sound.get_length():
			self._show_character_rom()
		elif self.phase == "rom_sways" and self.phase_seconds >= self.rom_appear_seconds + self.rom_sway_seconds:
			self.character_rom.rise_next_to(self.basic_rom, self.rom_join_seconds)
			self._enter("rom_joins")
		elif self.phase == "rom_joins" and not self.character_rom.is_gliding:
			self._clear_stage()
		elif self.phase == "clear_stage" and self.phase_seconds >= self.clear_stage_seconds:
			self._destroy_peddle()
			self._enter("typing")
		elif self.phase == "typing" and self.chip_listing.finished:
			self._enter("hold")
		elif self.phase == "hold" and self.phase_seconds >= self.final_hold_seconds:
			self._drop_pet()
		elif self.phase == "pet_drops":
			self.chip_listing.fade_lines(max(0.0, 1.0 - self.phase_seconds / self.pet_drop_seconds))
			self.chip_listing.vertical_offset = self._pet_drop_offset()
			if self.phase_seconds >= self.pet_drop_seconds:
				self._enter("done")

	def _drop_pet(self):
		self._enter("pet_drops")
		self.pet_drop_start_y = self.pet.world_center_point[1]
		self.pet.glide_center_to(self.pet.center_fractions_just_below_bottom_edge(), self.pet_drop_seconds,
		                         easing=ease_in_cubic)

	def _pet_drop_offset(self):
		if self.pet_drop_start_y is None:
			return 0.0
		return self.pet.world_center_point[1] - self.pet_drop_start_y

	def _start_pet_arrival(self):
		self._enter("pet_arrives")
		self.pet_sound.play()
		peddle_fraction_from_left, _ = self.chuck_peddle.center_screen_fractions
		self.chuck_peddle.glide_center_to(
			self.chuck_peddle.center_fractions_with_bottom_edge_on_screen_bottom(peddle_fraction_from_left),
			self.peddle_lower_seconds)
		_, pet_fraction_from_top = self.pet.center_fractions_with_bottom_edge_on_screen_bottom(0.0)
		self.pet.place_center_at(self.pet.center_fractions_just_beyond_left_edge(pet_fraction_from_top))
		self.pet.glide_center_to((self.pet_rest_fraction_from_left, pet_fraction_from_top), self.pet_enter_seconds,
		                         easing=ease_out_cubic)

	def _show_character_rom(self):
		self._enter("rom_sways")
		pet_right_edge = self.pet.center_screen_fractions[0] + self.pet.width_in_screen_widths / 2
		peddle_left_edge = self.chuck_peddle.center_screen_fractions[0] - self.chuck_peddle.width_in_screen_widths / 2
		self.character_rom.appear_at((pet_right_edge + peddle_left_edge) / 2, self.rom_fraction_from_top,
		                             self.rom_appear_seconds)

	def _clear_stage(self):
		self._enter("clear_stage")
		_, pet_fraction_from_top = self.pet.center_screen_fractions
		self.pet.glide_center_to(self.pet.center_fractions_with_left_edge_on_screen_left(pet_fraction_from_top),
		                         self.clear_stage_seconds)
		self.chuck_peddle.glide_center_to(self.chuck_peddle.center_fractions_just_below_bottom_edge(),
		                                  self.clear_stage_seconds, easing=ease_in_cubic)

	def _destroy_peddle(self):
		self.chuck_peddle.destroy()
		self.chuck_peddle = None
		self.peddle_destroyed = True

	def draw_pet(self):
		if self.pet_visible:
			self.pet.draw()

	def draw_overlay(self):
		self.chip_listing.draw()

	def destroy(self):
		self.pet_sound.stop()
		self.pet_picture.destroy()
		self.chip_listing.destroy()
		if self.chuck_peddle is not None:
			self._destroy_peddle()
