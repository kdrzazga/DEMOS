import os

import pygame
from OpenGL.GL import *

from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface
from lib.speech_bubble import SpeechBubble
from lib.typer import FONT_PATH

COMMODORE_HISTORY_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history", "c=")
BILL_GATES_IMAGE_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "bill.png")
BASIC_LICENSE_SOUND_PATH = os.path.join(COMMODORE_HISTORY_DIRECTORY, "77basic.mp3")
JACK_TRAMIEL_QUESTION_LINES = ("How much for this", "BASIC, Bill?")
BIG_JACK_HEAD_TOP_LEFT_PIXEL = (130, 15)


class SurfaceFadeOut:

	def __init__(self, picture_surface, fade_seconds):
		self.picture_surface = picture_surface
		self.fade_seconds = fade_seconds
		self.starting_opacity = picture_surface.opacity
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds
		self.picture_surface.opacity = self.starting_opacity * (1.0 - self.progress)

	@property
	def progress(self):
		return min(1.0, self.elapsed_seconds / self.fade_seconds)

	@property
	def finished(self):
		return self.elapsed_seconds >= self.fade_seconds


class BasicLicense:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.logo_fade_seconds = 1.0
		self.jack_shift_in_jack_widths = 0.5
		self.jack_shift_seconds = 1.0
		self.bill_height_in_screen_heights = 0.45
		self.bill_slide_seconds = 2.5
		self.bill_stop_fraction_from_left = 0.78
		self.jack_question_seconds = 5.5
		self.speech_bubble_font_size = 13
		self.speech_bubble_screen_margin = 0.3
		self.speech_bubble_shift_right_in_bubble_widths = 0.6
		self.speech_bubble_shift_down_in_bubble_heights = 0.6
		self.speech_bubble_nudge_up_in_screen_heights = 0.025
		self.speech_bubble_nudge_right_in_screen_heights = 0.075
		self.seconds_after_sound_before_exit = 0.5
		self.exit_seconds = 1.5
		self.bill_picture = PictureTexture.load(BILL_GATES_IMAGE_PATH)
		self.bill = PictureSurface(self.bill_picture, screen_plane, self.bill_height_in_screen_heights)
		self.bill_resting_fraction_from_top = self.bill.center_fractions_with_bottom_edge_on_screen_bottom(0.0)[1]
		self.jack_question_bubble = SpeechBubble(None, size=self.speech_bubble_font_size,
		                                         lines=JACK_TRAMIEL_QUESTION_LINES,
		                                         silent_seconds=self.jack_question_seconds, font_path=FONT_PATH)
		self.basic_license_sound = self._load_sound(BASIC_LICENSE_SOUND_PATH)
		self.talking_jack = None
		self.fading_logo = None
		self.logo_fade_out = None
		self.elapsed_seconds = 0.0
		self.bill_has_set_off = False
		self.jack_question_has_started = False
		self.exit_has_started = False

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	def begin(self, talking_jack, fading_logo):
		self.talking_jack = talking_jack
		self.fading_logo = fading_logo
		self.logo_fade_out = SurfaceFadeOut(fading_logo, self.logo_fade_seconds)
		self.elapsed_seconds = 0.0
		self.bill_has_set_off = False
		self.jack_question_has_started = False
		self.exit_has_started = False
		self.jack_question_bubble.started = False
		self.jack_question_bubble.visible = False
		self._shift_jack_left()
		self.bill.place_center_at(self.bill.center_fractions_just_beyond_right_edge(self.bill_resting_fraction_from_top))
		self.basic_license_sound.play()

	def _shift_jack_left(self):
		jack_fraction_from_left, jack_fraction_from_top = self.talking_jack.center_screen_fractions
		shift_in_screen_widths = self.talking_jack.width_in_screen_widths * self.jack_shift_in_jack_widths
		self.talking_jack.glide_center_to((jack_fraction_from_left - shift_in_screen_widths, jack_fraction_from_top),
		                                  self.jack_shift_seconds)

	def _send_bill_in(self):
		self.bill_has_set_off = True
		self.bill.glide_center_to((self.bill_stop_fraction_from_left, self.bill_resting_fraction_from_top),
		                          self.bill_slide_seconds, easing=ease_out_cubic)

	@property
	def jack_question_start_second(self):
		return self.jack_shift_seconds + self.bill_slide_seconds

	@property
	def talk_finished(self):
		return self.elapsed_seconds >= self.basic_license_sound.get_length()

	@property
	def exit_start_second(self):
		return self.basic_license_sound.get_length() + self.seconds_after_sound_before_exit

	@property
	def total_seconds(self):
		return self.exit_start_second + self.exit_seconds

	def _drop_all_pictures_below_screen(self):
		self.exit_has_started = True
		for leaving_picture in (self.talking_jack, self.bill, self.fading_logo):
			leaving_picture.glide_center_to(leaving_picture.center_fractions_just_below_bottom_edge(), self.exit_seconds,
			                                easing=ease_in_cubic)

	@property
	def done(self):
		return self.elapsed_seconds >= self.total_seconds

	def update(self, seconds):
		self.elapsed_seconds += seconds
		self.logo_fade_out.update(seconds)
		self.talking_jack.update(seconds)
		if not self.bill_has_set_off and self.elapsed_seconds >= self.jack_shift_seconds:
			self._send_bill_in()
		self.bill.update(seconds)
		if not self.jack_question_has_started and self.elapsed_seconds >= self.jack_question_start_second:
			self.jack_question_has_started = True
			self.jack_question_bubble.start()
		if not self.exit_has_started and self.elapsed_seconds >= self.exit_start_second:
			self._drop_all_pictures_below_screen()
		self.jack_question_bubble.update(seconds)

	def draw(self):
		if self.bill_has_set_off:
			self.bill.draw()
		self._draw_question_bubble_left_of_jack_head()

	def _question_bubble_anchor_kept_on_screen(self):
		head_top_left_x, head_top_left_y = self.talking_jack.world_point_from_picture_pixel(*BIG_JACK_HEAD_TOP_LEFT_PIXEL)
		bubble_offset_x = self.jack_question_bubble.offset[0]
		bubble_width = self.jack_question_bubble.world_width
		screen_left_x = -self.screen_plane.visible_width / 2 + self.speech_bubble_screen_margin
		bubble_left_x = max(head_top_left_x - bubble_offset_x - bubble_width, screen_left_x)
		bubble_left_x += bubble_width * self.speech_bubble_shift_right_in_bubble_widths
		bubble_shift_down = self.jack_question_bubble.world_height * self.speech_bubble_shift_down_in_bubble_heights
		nudge_up = self.speech_bubble_nudge_up_in_screen_heights * self.screen_plane.visible_height
		nudge_right = self.speech_bubble_nudge_right_in_screen_heights * self.screen_plane.visible_height
		return bubble_left_x - bubble_offset_x + nudge_right, head_top_left_y - bubble_shift_down + nudge_up

	def _draw_question_bubble_left_of_jack_head(self):
		anchor_x, anchor_y = self._question_bubble_anchor_kept_on_screen()
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.jack_question_bubble.draw(anchor_x, anchor_y, -self.screen_plane.camera_distance)
		glPopMatrix()

	def destroy(self):
		self.basic_license_sound.stop()
		self.bill_picture.destroy()
		self.jack_question_bubble.release()
