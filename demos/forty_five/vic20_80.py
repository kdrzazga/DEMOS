import os

from demos.forty_five.computer_with_chip_listing import ComputerWithChipListing
from demos.forty_five.paths import COMMODORE_HISTORY_DIRECTORY, COMMON_COMMODORE_DIRECTORY

VIC20_IMAGE_PATH = os.path.join(COMMON_COMMODORE_DIRECTORY, "vic20.png")
VIC20_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "80VIC-20.mp3")
VIC20_CHIPS_HEADER = "Chips used in VIC-20:"
VIC20_CHIP_NAMES = ("Processor 6502", "VIA (I/O chip)", "BASIC ROM", "Character ROM", "KERNAL ROM",
                    "VIC (MOS 6560)")
VIC20_CHIP_LINE_TARGETS = ((0.25, 0.1), (0.35, 0.1), (0.45, 0.1), (0.55, 0.1), (0.65, 0.1), (0.75, 0.1))


class Vic20Arrival(ComputerWithChipListing):

	def __init__(self, screen_plane):
		self.vic20_height_in_screen_heights = 0.4
		super().__init__(screen_plane, VIC20_IMAGE_PATH, VIC20_SOUND_PATH, self.vic20_height_in_screen_heights,
		                 VIC20_CHIPS_HEADER, VIC20_CHIP_NAMES, VIC20_CHIP_LINE_TARGETS)
		self.wait_seconds = 2.0
		self.listing_hold_seconds = 4.0
		self.chip_listing_raise_in_lines = 2
		self.chip_listing.raise_by_lines(self.chip_listing_raise_in_lines)

	def begin(self):
		self._enter("wait")

	@property
	def playback_finished(self):
		return self.phase in ("arrived", "typing", "hold", "computer_drops", "done")

	@property
	def waits_for_chip_list(self):
		return self.phase == "arrived"

	def list_chips(self, chip_animations):
		self.chip_listing.begin(chip_animations)
		self._enter("typing")

	def _start_computer_arrival(self):
		self._send_computer_in_from_left(self.computer.center_fractions_with_left_edge_on_screen_left(
			self._fraction_from_top_standing_on_screen_bottom))

	def _continue_after_computer_sound(self):
		self._enter("arrived")
