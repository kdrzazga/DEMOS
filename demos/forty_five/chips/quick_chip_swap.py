import os

import pygame
from OpenGL.GL import *

from demos.forty_five.chips.chip_name_flash import ChipNameFlash
from demos.forty_five.font import FONT_PATH
from lib.typing_effect.typed_label import TypedLabel

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIA_SOUND_PATH = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=", "CIA.mp3")
CIA_SWAP_CAPTION = "VIA (6522) -> CIA (6526)"
CIA_SWAP_PREDECESSOR_NAME = "VIA"


class QuickChipSwap:

	def __init__(self, screen_plane, sound_path, caption, predecessor_name):
		self.screen_plane = screen_plane
		self.predecessor_name = predecessor_name
		self.predecessor_name_flash = None
		self.swap_seconds = 3.0
		self.caption_height = 0.5
		self.caption_frames_per_letter = 4
		self.swap_sound = self._load_sound(sound_path)
		self.caption_label = TypedLabel(caption, self.caption_height, frames_per_letter=self.caption_frames_per_letter,
		                                font_path=FONT_PATH)
		self.caption_label.build()
		self.newcomer = None
		self.predecessor = None
		self.place_of_predecessor = None
		self.sound_seconds = 0.0
		self.phase = "idle"

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	@property
	def done(self):
		return self.phase == "done"

	def begin(self, newcomer, predecessor):
		self.newcomer = newcomer
		self.predecessor = predecessor
		self.place_of_predecessor = predecessor.resting_pose.copy()
		self.sound_seconds = 0.0
		self.caption_label.restart()
		self.swap_sound.play()
		self.predecessor_name_flash = ChipNameFlash.before_gallery_removal(predecessor,self.predecessor_name)
		self.predecessor_name_flash.build()
		self.predecessor_name_flash.start()
		self.phase = "naming_predecessor"

	def update(self, seconds):
		self.sound_seconds += seconds
		self.predecessor_name_flash.update(seconds)
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
		elif self.phase == "waiting_for_sound" and self._sound_and_caption_finished:
			self.phase = "done"

	@property
	def _sound_and_caption_finished(self):
		return self.sound_seconds >= self.swap_sound.get_length() and self.caption_label.finished

	def draw_overlay(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.caption_label.draw((0.0, 0.0, -self.screen_plane.camera_distance), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
		glPopMatrix()
		glPopAttrib()
		self.predecessor_name_flash.draw()

	def destroy(self):
		self.swap_sound.stop()
		self.caption_label.destroy()
		if self.predecessor_name_flash:
			self.predecessor_name_flash.destroy()
