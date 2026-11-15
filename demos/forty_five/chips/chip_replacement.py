import os

from demos.forty_five.chips.chip_swap import ChipSwap
from demos.forty_five.paths import COMMODORE_HISTORY_DIRECTORY
from demos.forty_five.typed_lines import TypedLines, built_typed_label, draw_label_facing_screen

MOS6510_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "6510.mp3")
MOS6510_TEXT_LINES = ("MOS 6510 was supposed to replace", "its older buddy 6502")
MOS6510_PREDECESSOR_NAME = "  6502"
VIC_II_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "VIC2.mp3")
VIC_II_TEXT_LINES = ("VIC-II : higher resolution,", "8 sprites, raster")
VIC_II_PREDECESSOR_NAME = "VIC"


class ChipReplacement(ChipSwap):

	def __init__(self, screen_plane, sound_path, text_lines, predecessor_name):
		super().__init__(screen_plane, sound_path, predecessor_name)
		self.drive_in_seconds = 6.0
		self.chip_height_in_photo_heights = 0.8
		self.take_place_seconds = 2.5
		self.predecessor_leave_seconds = 1.5
		self.text_line_height = 0.6
		self.text_line_gap = 0.3
		self.text_frames_per_letter = 4
		self.text_top_line_y = -2.4
		self.typed_lines = TypedLines(built_typed_label(text, self.text_line_height, self.text_frames_per_letter)
		                              for text in text_lines)

	def _begin_choreography(self):
		self.typed_lines.restart()
		self.newcomer.drive_to_screen_centre_turning_horizontal(self.drive_in_seconds, self.chip_height_in_photo_heights)
		self.phase = "drive_in"

	def _advance_choreography(self):
		if self.phase == "drive_in" and not self.newcomer.is_gliding:
			self.phase = "typing"
		elif self.phase == "typing":
			self._advance_typing()
		elif self.phase == "listening":
			self._name_predecessor_as_sound_ends()
		elif self.phase == "swap" and not self.newcomer.is_gliding and self.predecessor.has_left_through_top_edge:
			self.phase = "done"

	def _advance_typing(self):
		self.typed_lines.update()
		if self.typed_lines.finished:
			self.phase = "listening"

	def _name_predecessor_as_sound_ends(self):
		name_flash = self.predecessor_name_flash
		if not name_flash.started and self._seconds_of_sound_left <= name_flash.duration_seconds:
			name_flash.start()
		if name_flash.finished and self._seconds_of_sound_left <= 0.0:
			self._swap_chips()

	def _swap_chips(self):
		place_of_predecessor = self.predecessor.resting_pose.copy()
		self.predecessor.leave_through_top_edge(self.predecessor_leave_seconds)
		self.newcomer.take_place_turning_vertical(place_of_predecessor, self.take_place_seconds)
		self.phase = "swap"

	def _caption_is_visible(self):
		return self.phase not in ("idle", "drive_in")

	def _draw_caption(self):
		line_step = self.text_line_height + self.text_line_gap
		for index, label in enumerate(self.typed_lines.labels):
			draw_label_facing_screen(label, 0.0, self.text_top_line_y - index * line_step, self.screen_plane)

	def _destroy_caption(self):
		self.typed_lines.destroy()
