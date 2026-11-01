import os

import pygame
from OpenGL.GL import *

from demos.forty_five.typed_label import TypedLabel

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
COMMODORE_HISTORY_DIRECTORY = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=")
MOS6510_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "6510.mp3")
MOS6510_TEXT_LINES = ("MOS 6510 was supposed to replace", "its older buddy 6502")
VIC_II_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "VIC2.mp3")
VIC_II_TEXT_LINES = ("VIC-II : higher resolution,", "8 sprites, raster")


class ChipReplacement:

	def __init__(self, screen_plane, sound_path, text_lines):
		self.screen_plane = screen_plane
		self.drive_in_seconds = 6.0
		self.chip_height_in_photo_heights = 0.8
		self.take_place_seconds = 2.5
		self.predecessor_leave_seconds = 1.5
		self.text_line_height = 0.6
		self.text_line_gap = 0.3
		self.text_frames_per_letter = 4
		self.text_top_line_y = -2.4
		self.replacement_sound = self._load_sound(sound_path)
		self.text_labels = tuple(TypedLabel(text, self.text_line_height, frames_per_letter=self.text_frames_per_letter)
		                         for text in text_lines)
		for label in self.text_labels:
			label.build()
		self.newcomer = None
		self.predecessor = None
		self.sound_seconds = 0.0
		self.typing_index = 0
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
		for label in self.text_labels:
			label.restart()
		self.typing_index = 0
		self.sound_seconds = 0.0
		self.replacement_sound.play()
		self.newcomer.drive_to_screen_centre_turning_horizontal(self.drive_in_seconds, self.chip_height_in_photo_heights)
		self.phase = "drive_in"

	def update(self, seconds):
		self.sound_seconds += seconds
		if self.phase == "drive_in" and not self.newcomer.is_gliding:
			self.phase = "typing"
		elif self.phase == "typing":
			self._advance_typing()
		elif self.phase == "listening" and self.sound_seconds >= self.replacement_sound.get_length():
			self._swap_chips()
		elif self.phase == "swap" and not self.newcomer.is_gliding and self.predecessor.has_left_through_top_edge:
			self.phase = "done"

	def _advance_typing(self):
		label = self.text_labels[self.typing_index]
		label.update()
		if not label.finished:
			return
		if self.typing_index + 1 < len(self.text_labels):
			self.typing_index += 1
		else:
			self.phase = "listening"

	def _swap_chips(self):
		place_of_predecessor = self.predecessor.resting_pose.copy()
		self.predecessor.leave_through_top_edge(self.predecessor_leave_seconds)
		self.newcomer.take_place_turning_vertical(place_of_predecessor, self.take_place_seconds)
		self.phase = "swap"

	def draw_overlay(self):
		if self.phase in ("idle", "drive_in"):
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		line_step = self.text_line_height + self.text_line_gap
		depth = -self.screen_plane.camera_distance
		for index, label in enumerate(self.text_labels):
			label.draw((0.0, self.text_top_line_y - index * line_step, depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		self.replacement_sound.stop()
		for label in self.text_labels:
			label.destroy()
