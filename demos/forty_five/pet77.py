import os

from demos.forty_five.computer_with_chip_listing import ComputerWithChipListing
from demos.forty_five.paths import COMMODORE_HISTORY_DIRECTORY, COMMON_COMMODORE_DIRECTORY
from lib.flying_logo import ease_in_cubic

PET_IMAGE_PATH = os.path.join(COMMON_COMMODORE_DIRECTORY, "pet.png")
PET_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "77PET.mp3")
PET_CHIPS_HEADER = "Chips used in PET:"
PET_CHIP_NAMES = ("Processor 6502", "PIA (I/O support)", "VIA (I/O support)", "BASIC ROM", "Character ROM",
                  "KERNAL ROM")
PET_CHIP_LINE_TARGETS = ((0.25, 0.05), (0.35, 0.05), (0.45, 0.05), (0.55, 0.05), (0.65, 0.05), (0.75, 0.05))


class PetIntroduction(ComputerWithChipListing):

	def __init__(self, screen_plane):
		self.pet_height_in_screen_heights = 0.5
		super().__init__(screen_plane, PET_IMAGE_PATH, PET_SOUND_PATH, self.pet_height_in_screen_heights,
		                 PET_CHIPS_HEADER, PET_CHIP_NAMES, PET_CHIP_LINE_TARGETS)
		self.wait_seconds = 1.0
		self.listing_hold_seconds = 2.0
		self.pet_rest_fraction_from_left = 0.28
		self.peddle_lower_seconds = 2.0
		self.rom_appear_seconds = 0.4
		self.rom_sway_seconds = 2.0
		self.rom_join_seconds = 2.0
		self.rom_fraction_from_top = 0.72
		self.gap_between_appearing_roms_fraction = 0.02
		self.clear_stage_seconds = 1.5
		self.chuck_peddle = None
		self.basic_rom = None
		self.character_rom = None
		self.kernal_rom = None
		self.peddle_destroyed = False

	def begin(self, chuck_peddle, processor, pia, via, basic_rom, character_rom, kernal_rom):
		self.chuck_peddle = chuck_peddle
		self.basic_rom = basic_rom
		self.character_rom = character_rom
		self.kernal_rom = kernal_rom
		self.peddle_destroyed = False
		self.chip_listing.begin((processor, pia, via, basic_rom, character_rom, kernal_rom))
		self._enter("wait")

	def _start_computer_arrival(self):
		peddle_fraction_from_left, _ = self.chuck_peddle.center_screen_fractions
		self.chuck_peddle.glide_center_to(
			self.chuck_peddle.center_fractions_with_bottom_edge_on_screen_bottom(peddle_fraction_from_left),
			self.peddle_lower_seconds)
		self._send_computer_in_from_left((self.pet_rest_fraction_from_left,
		                                  self._fraction_from_top_standing_on_screen_bottom))

	def _continue_after_computer_sound(self):
		self._enter("rom_sways")
		pet_right_edge = self.computer.center_screen_fractions[0] + self.computer.width_in_screen_widths / 2
		peddle_left_edge = self.chuck_peddle.center_screen_fractions[0] - self.chuck_peddle.width_in_screen_widths / 2
		middle_between_pet_and_peddle = (pet_right_edge + peddle_left_edge) / 2
		half_rom_spacing = (self._width_fraction_of_appeared_rom() + self.gap_between_appearing_roms_fraction) / 2
		self.character_rom.appear_at(middle_between_pet_and_peddle - half_rom_spacing, self.rom_fraction_from_top,
		                             self.rom_appear_seconds)
		self.kernal_rom.appear_at(middle_between_pet_and_peddle + half_rom_spacing, self.rom_fraction_from_top,
		                          self.rom_appear_seconds)

	def _width_fraction_of_appeared_rom(self):
		self.character_rom.appear_at(0.5, self.rom_fraction_from_top, self.rom_appear_seconds)
		rom_width_fraction, _ = self.character_rom.screen_size_fractions(self.character_rom.resting_pose)
		return rom_width_fraction

	def _advance_own_phases(self):
		if self.phase == "rom_sways" and self.phase_seconds >= self.rom_appear_seconds + self.rom_sway_seconds:
			self.character_rom.rise_next_to(self.basic_rom, self.rom_join_seconds)
			self.kernal_rom.rise_next_to(self.character_rom, self.rom_join_seconds)
			self._enter("rom_joins")
		elif self.phase == "rom_joins" and not self.character_rom.is_gliding and not self.kernal_rom.is_gliding:
			self._clear_stage()
		elif self.phase == "clear_stage" and self.phase_seconds >= self.clear_stage_seconds:
			self._destroy_peddle()
			self._enter("typing")

	def _clear_stage(self):
		self._enter("clear_stage")
		_, pet_fraction_from_top = self.computer.center_screen_fractions
		self.computer.glide_center_to(
			self.computer.center_fractions_with_left_edge_on_screen_left(pet_fraction_from_top), self.clear_stage_seconds)
		self.chuck_peddle.glide_center_to(self.chuck_peddle.center_fractions_just_below_bottom_edge(),
		                                  self.clear_stage_seconds, easing=ease_in_cubic)

	def _destroy_peddle(self):
		self.chuck_peddle.destroy()
		self.chuck_peddle = None
		self.peddle_destroyed = True

	def destroy(self):
		super().destroy()
		if self.chuck_peddle is not None:
			self._destroy_peddle()
