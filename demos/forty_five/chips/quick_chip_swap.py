import os

from demos.forty_five.chips.chip_swap import ChipSwap
from demos.forty_five.paths import COMMODORE_HISTORY_DIRECTORY
from demos.forty_five.typed_lines import built_typed_label, draw_label_facing_screen

CIA_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "CIA.mp3")
CIA_SWAP_CAPTION = "VIA (6522) -> CIA (6526)"
CIA_SWAP_PREDECESSOR_NAME = "VIA"


class QuickChipSwap(ChipSwap):

	def __init__(self, screen_plane, sound_path, caption, predecessor_name):
		super().__init__(screen_plane, sound_path, predecessor_name)
		self.swap_seconds = 3.0
		self.caption_height = 0.5
		self.caption_frames_per_letter = 4
		self.caption_label = built_typed_label(caption, self.caption_height, self.caption_frames_per_letter)
		self.place_of_predecessor = None

	def _begin_choreography(self):
		self.place_of_predecessor = self.predecessor.resting_pose.copy()
		self.caption_label.restart()
		self.predecessor_name_flash.start()
		self.phase = "naming_predecessor"

	def _advance_choreography(self):
		if not self.caption_label.finished:
			self.caption_label.update()
		if self.phase == "naming_predecessor" and self.predecessor_name_flash.finished:
			self.predecessor.leave_through_top_edge(self.swap_seconds / 2)
			self.phase = "predecessor_leaves"
		elif self.phase == "predecessor_leaves" and self.predecessor.has_left_through_top_edge:
			self.newcomer.drop_in_from_top_edge_to(self.place_of_predecessor, self.swap_seconds / 2)
			self.phase = "newcomer_drops_in"
		elif self.phase == "newcomer_drops_in" and not self.newcomer.is_gliding:
			self.phase = "waiting_for_sound"
		elif self.phase == "waiting_for_sound" and self._seconds_of_sound_left <= 0.0 and self.caption_label.finished:
			self.phase = "done"

	def _draw_caption(self):
		draw_label_facing_screen(self.caption_label, 0.0, 0.0, self.screen_plane)

	def _destroy_caption(self):
		self.caption_label.destroy()
