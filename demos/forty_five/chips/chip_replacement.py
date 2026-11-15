import os

from demos.forty_five.chips.chip_name_flash import ChipNameFlash
from demos.forty_five.overlay import screen_overlay
from demos.forty_five.paths import COMMODORE_HISTORY_DIRECTORY
from demos.forty_five.sound import load_sound
from demos.forty_five.typed_lines import TypedLines, built_typed_label, draw_label_facing_screen

MOS6510_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "6510.mp3")
MOS6510_TEXT_LINES = ("MOS 6510 was supposed to replace", "its older buddy 6502")
MOS6510_PREDECESSOR_NAME = "  6502"
VIC_II_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "VIC2.mp3")
VIC_II_TEXT_LINES = ("VIC-II : higher resolution,", "8 sprites, raster")
VIC_II_PREDECESSOR_NAME = "VIC"


class ChipReplacement:

	def __init__(self, screen_plane, sound_path, text_lines, predecessor_name):
		self.screen_plane = screen_plane
		self.predecessor_name = predecessor_name
		self.predecessor_name_flash = None
		self.drive_in_seconds = 6.0
		self.chip_height_in_photo_heights = 0.8
		self.take_place_seconds = 2.5
		self.predecessor_leave_seconds = 1.5
		self.text_line_height = 0.6
		self.text_line_gap = 0.3
		self.text_frames_per_letter = 4
		self.text_top_line_y = -2.4
		self.replacement_sound = load_sound(sound_path)
		self.typed_lines = TypedLines(built_typed_label(text, self.text_line_height, self.text_frames_per_letter)
		                              for text in text_lines)
		self.newcomer = None
		self.predecessor = None
		self.sound_seconds = 0.0
		self.phase = "idle"

	@property
	def done(self):
		return self.phase == "done"

	def begin(self, newcomer, predecessor):
		self.newcomer = newcomer
		self.predecessor = predecessor
		self.predecessor_name_flash = ChipNameFlash.before_gallery_removal(predecessor,self.predecessor_name)
		self.predecessor_name_flash.build()
		self.typed_lines.restart()
		self.sound_seconds = 0.0
		self.replacement_sound.play()
		self.newcomer.drive_to_screen_centre_turning_horizontal(self.drive_in_seconds, self.chip_height_in_photo_heights)
		self.phase = "drive_in"

	def update(self, seconds):
		self.sound_seconds += seconds
		self.predecessor_name_flash.update(seconds)
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
		seconds_of_sound_left = self.replacement_sound.get_length() - self.sound_seconds
		name_flash = self.predecessor_name_flash
		if not name_flash.started and seconds_of_sound_left <= name_flash.duration_seconds:
			name_flash.start()
		if name_flash.finished and seconds_of_sound_left <= 0.0:
			self._swap_chips()

	def _swap_chips(self):
		place_of_predecessor = self.predecessor.resting_pose.copy()
		self.predecessor.leave_through_top_edge(self.predecessor_leave_seconds)
		self.newcomer.take_place_turning_vertical(place_of_predecessor, self.take_place_seconds)
		self.phase = "swap"

	def draw_overlay(self):
		if self.phase in ("idle", "drive_in"):
			return
		line_step = self.text_line_height + self.text_line_gap
		with screen_overlay():
			for index, label in enumerate(self.typed_lines.labels):
				draw_label_facing_screen(label, 0.0, self.text_top_line_y - index * line_step, self.screen_plane)
		self.predecessor_name_flash.draw()

	def destroy(self):
		self.replacement_sound.stop()
		self.typed_lines.destroy()
		if self.predecessor_name_flash:
			self.predecessor_name_flash.destroy()
