import os

import pygame
from OpenGL.GL import *

from lib.speech_bubble import SpeechBubble
from lib.typer import FONT_PATH
from demos.forty_five.mos_team75 import MosTeamFactory

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SID_SOUND_PATH = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=", "SID.mp3")
ROBERT_YANNES_SPEECH_LINES = ("I'd worked with synthetizes", "and I wanted a chip that was", "a music synthetizer.")


class RobertYannesIntroduction:

	def __init__(self, screen_plane, aspect_ratio, field_of_view_degrees):
		self.screen_plane = screen_plane
		self.sid_arrival_second = 1.0
		self.sid_slide_in_seconds = 1.5
		self.sid_height_in_photo_heights = 0.75
		self.sid_travel_second = 3.0
		self.sid_travel_seconds = 2.0
		self.speech_start_second = 4.0
		self.speech_bubble_font_size = 13
		self.speech_bubble_anchor_fraction_from_picture_bottom = 0.5
		self.photo_exit_seconds = 1.5
		self.show = MosTeamFactory.create_robert_yannes_show(aspect_ratio, field_of_view_degrees)
		self.sid_sound = self._load_sound(SID_SOUND_PATH)
		self.speech_bubble = SpeechBubble(None, size=self.speech_bubble_font_size, lines=ROBERT_YANNES_SPEECH_LINES,
		                                  font_path=FONT_PATH)
		self.sid_chip = None
		self.gallery_neighbour = None
		self.elapsed_seconds = 0.0
		self.sid_has_arrived = False
		self.sid_has_set_off = False

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	@property
	def done(self):
		return self.show.has_left and not self.sid_chip.is_gliding

	def begin(self, sid_chip, gallery_neighbour):
		self.sid_chip = sid_chip
		self.gallery_neighbour = gallery_neighbour
		self.elapsed_seconds = 0.0
		self.sid_has_arrived = False
		self.sid_has_set_off = False
		self.speech_bubble.started = False
		self.speech_bubble.visible = False
		self.show.restart()
		self.sid_sound.play()

	def update(self, seconds):
		self.elapsed_seconds += seconds
		self.show.update(seconds)
		self.speech_bubble.update(seconds)
		if self.elapsed_seconds >= self.sid_arrival_second and not self.sid_has_arrived:
			self.sid_has_arrived = True
			middle_right_of_picture = (self.show.picture_right_edge_screen_fraction + 1.0) / 2
			self.sid_chip.slide_in_from_right(middle_right_of_picture, self.sid_slide_in_seconds,
			                                  self.sid_height_in_photo_heights)
		if self.elapsed_seconds >= self.sid_travel_second and not self.sid_has_set_off:
			self.sid_has_set_off = True
			self.sid_chip.rise_next_to(self.gallery_neighbour, self.sid_travel_seconds)
		if self.elapsed_seconds >= self.speech_start_second and not self.speech_bubble.started:
			self.speech_bubble.start()
		sound_has_ended = self.elapsed_seconds >= self.sid_sound.get_length()
		if self.show.done and sound_has_ended and not self.show.is_leaving:
			self.speech_bubble.stop()
			self.show.leave_through_bottom(self.photo_exit_seconds)

	def draw(self):
		self.show.draw()
		anchor_x, anchor_y = self.show.picture_right_edge_point_on_plane_at(
			self.screen_plane.camera_distance, self.speech_bubble_anchor_fraction_from_picture_bottom)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.speech_bubble.draw(anchor_x, anchor_y, -self.screen_plane.camera_distance)
		glPopMatrix()

	def destroy(self):
		self.sid_sound.stop()
		self.show.destroy()
		self.speech_bubble.release()
