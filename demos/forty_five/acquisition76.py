import os

import pygame
from OpenGL.GL import *

from lib.caption_sequence import CaptionSequence
from lib.flying_logo import ease_out_cubic
from lib.laser_line import PictureTexture, smooth_step
from lib.morphing_caption import MorphingCaption
from lib.picture_surface import PictureSurface
from lib.speech_bubble import SpeechBubble
from lib.typer import FONT_PATH

HISTORY_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history")
JABBA_IMAGE_PATH = os.path.join(HISTORY_DIRECTORY, "c=", "jabba.png")
JACK_TRAMIEL_IMAGE_PATH = os.path.join(HISTORY_DIRECTORY, "c=", "Jack.png")
JACK_TRAMIEL_BIG_IMAGE_PATH = os.path.join(HISTORY_DIRECTORY, "c=", "JackBig.png")
JACK_PICTURE_TOP_LEFT_PIXEL_INSIDE_BIG_PICTURE = (121, 0)
MOS_LOGO_IMAGE_PATH = os.path.join(HISTORY_DIRECTORY, "mos", "logo.png")
JABBA_TO_JACK_CAPTION_SEGMENTS = (("Ja", "Ja"), ("bba", "ck"), (" T", " T"), ("he Hutt", "ramiel"))
JACK_TRAMIEL_SPEECH_LINES = ("Time to buy", "MOS Technology")
ACQUISITION_YEAR_FLASHES = ("1976", "1976", "1976")


class MosAcquisition:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.jabba_height_in_screen_heights = 0.2
		self.jabba_arrival_delay_seconds = 1.0
		self.jabba_arrival_seconds = 4.0
		self.jabba_stop_fraction_from_left = 0.4
		self.jabba_fraction_from_top = 0.55
		self.jabba_swing_amplitude_degrees = 25.0
		self.jabba_swing_period_seconds = 1.6
		self.pause_seconds_before_morph = 0.5
		self.picture_crossfade_seconds = 2.0
		self.shrink_seconds = 1.0
		self.caption_height_in_screen_heights = 0.035
		self.caption_gap = 0.02 * screen_plane.visible_height
		self.logo_width_in_jack_widths = 2.0
		self.logo_stop_fraction_from_left = 0.6
		self.speech_bubble_font_size = 15
		self.speech_seconds = 2.5
		self.year_flash_seconds = 0.5
		self.pause_seconds_between_year_flashes = 0.25
		self.year_flash_color = (230, 40, 40)
		self.year_flash_font_pixel_size = 110
		self.year_flash_margin_from_top_left_pixels = (170.0, 110.0)
		self.year_flash_gap_below_chips_pixels = 30.0
		self.design_screen_height = 800.0
		self.hold_seconds_after_speech = 1.0
		self.big_jack_fade_seconds = 0.4
		self.hold_seconds_after_big_jack = 2.0
		self.jabba_picture = PictureTexture.load(JABBA_IMAGE_PATH)
		jack_surface = pygame.image.load(JACK_TRAMIEL_IMAGE_PATH).convert_alpha()
		self.jack_pixel_size = jack_surface.get_size()
		self.jack_shrunk_width_scale = jack_surface.get_width() / self.jabba_picture.pixel_width
		self.jack_stretched_to_jabba_width_picture = PictureTexture(pygame.transform.smoothscale(
			jack_surface, (self.jabba_picture.pixel_width, jack_surface.get_height())))
		self.portrait = PictureSurface(self.jabba_picture, screen_plane, self.jabba_height_in_screen_heights,
		                               swing_amplitude_degrees=self.jabba_swing_amplitude_degrees,
		                               swing_period_seconds=self.jabba_swing_period_seconds)
		self.caption = MorphingCaption(JABBA_TO_JACK_CAPTION_SEGMENTS,
		                               self.caption_height_in_screen_heights * screen_plane.visible_height)
		self.mos_logo = self._build_mos_logo()
		self.world_units_per_jack_pixel = self.portrait.picture_height / self.jack_pixel_size[1]
		self.big_jack_picture = PictureTexture.load(JACK_TRAMIEL_BIG_IMAGE_PATH)
		self.big_jack = PictureSurface(self.big_jack_picture, screen_plane, self.big_jack_picture.pixel_height
		                               * self.world_units_per_jack_pixel / screen_plane.visible_height)
		self.jack_speech_bubble = SpeechBubble(None, size=self.speech_bubble_font_size, lines=JACK_TRAMIEL_SPEECH_LINES,
		                                       silent_seconds=self.speech_seconds, font_path=FONT_PATH)
		self.year_flashes = CaptionSequence(ACQUISITION_YEAR_FLASHES, seconds_per_caption=self.year_flash_seconds,
		                                    pause_seconds_between_captions=self.pause_seconds_between_year_flashes,
		                                    text_color=self.year_flash_color,
		                                    screen_scale=glGetIntegerv(GL_VIEWPORT)[3] / self.design_screen_height,
		                                    font_pixel_size=self.year_flash_font_pixel_size,
		                                    margin_from_top_left_pixels=self.year_flash_margin_from_top_left_pixels,
		                                    font_path=FONT_PATH)
		self.restart()

	def place_year_flashes_below(self, chips_bottom_fraction_from_top):
		screen_scale = glGetIntegerv(GL_VIEWPORT)[3] / self.design_screen_height
		left_margin_pixels, _ = self.year_flash_margin_from_top_left_pixels
		top_margin_pixels = chips_bottom_fraction_from_top * self.design_screen_height + self.year_flash_gap_below_chips_pixels
		self.year_flashes.margin_from_top_left_pixels = (left_margin_pixels * screen_scale, top_margin_pixels * screen_scale)

	def _build_mos_logo(self):
		logo_picture = PictureTexture.load(MOS_LOGO_IMAGE_PATH)
		jack_width = self.portrait.picture_width * self.jack_shrunk_width_scale
		logo_height = jack_width * self.logo_width_in_jack_widths / logo_picture.aspect_ratio
		return PictureSurface(logo_picture, self.screen_plane, logo_height / self.screen_plane.visible_height)

	def restart(self):
		self.elapsed_seconds = 0.0
		self.jabba_has_set_off = False
		self.morph_has_started = False
		self.speech_has_started = False
		self.big_jack_reveal_seconds = None
		self.portrait.opacity = 1.0
		self.mos_logo.opacity = 1.0
		self.portrait.show_picture(self.jabba_picture)
		self.portrait.place_center_at(self.portrait.center_fractions_just_beyond_left_edge(self.jabba_fraction_from_top))
		self.mos_logo.place_center_at(self.mos_logo.center_fractions_just_beyond_right_edge(self.jabba_fraction_from_top))
		self.jack_speech_bubble.started = False
		self.jack_speech_bubble.visible = False
		self.year_flashes.reset()

	@property
	def morph_start_second(self):
		return self.jabba_arrival_delay_seconds + self.jabba_arrival_seconds + self.pause_seconds_before_morph

	@property
	def shrink_start_second(self):
		return self.morph_start_second + self.picture_crossfade_seconds

	@property
	def morph_end_second(self):
		return self.shrink_start_second + self.shrink_seconds

	@property
	def total_seconds(self):
		speech_and_flashes_seconds = max(self.speech_seconds, self.year_flashes.total_seconds)
		return self.morph_end_second + speech_and_flashes_seconds + self.hold_seconds_after_speech

	@property
	def morph_finished(self):
		return self.elapsed_seconds >= self.morph_end_second

	@property
	def big_jack_revealed(self):
		return self.big_jack_reveal_seconds is not None

	@property
	def big_jack_opacity(self):
		if not self.big_jack_revealed:
			return 0.0
		return min(1.0, self.big_jack_reveal_seconds / self.big_jack_fade_seconds)

	@property
	def done(self):
		if not self.big_jack_revealed:
			return False
		big_jack_has_been_held = self.big_jack_reveal_seconds >= self.big_jack_fade_seconds + self.hold_seconds_after_big_jack
		return self.elapsed_seconds >= self.total_seconds and big_jack_has_been_held

	def reveal_big_jack(self):
		self.big_jack_reveal_seconds = 0.0
		self.big_jack.place_center_at(self._big_jack_center_fractions_matching_jack_head())
		self.big_jack_center_when_revealed = self.big_jack.world_center_point

	def _how_far_big_jack_moved_since_reveal(self):
		if not self.big_jack_revealed:
			return 0.0, 0.0
		current_x, current_y = self.big_jack.world_center_point
		revealed_x, revealed_y = self.big_jack_center_when_revealed
		return current_x - revealed_x, current_y - revealed_y

	def _big_jack_center_fractions_matching_jack_head(self):
		jack_pixel_width, jack_pixel_height = self.jack_pixel_size
		jack_left_pixel, jack_top_pixel = JACK_PICTURE_TOP_LEFT_PIXEL_INSIDE_BIG_PICTURE
		jack_center_inside_big_x = jack_left_pixel + jack_pixel_width / 2
		jack_center_inside_big_y = jack_top_pixel + jack_pixel_height / 2
		shift_right_pixels = self.big_jack_picture.pixel_width / 2 - jack_center_inside_big_x
		shift_down_pixels = self.big_jack_picture.pixel_height / 2 - jack_center_inside_big_y
		portrait_center_x, portrait_center_y = self.portrait.world_center_point
		return self.screen_plane.screen_fractions_from_world_point(
			portrait_center_x + shift_right_pixels * self.world_units_per_jack_pixel,
			portrait_center_y - shift_down_pixels * self.world_units_per_jack_pixel)

	@property
	def caption_morph_progress(self):
		seconds_into_morph = self.elapsed_seconds - self.morph_start_second
		return smooth_step(max(0.0, min(1.0, seconds_into_morph / (self.morph_end_second - self.morph_start_second))))

	@property
	def shrink_progress(self):
		seconds_into_shrink = self.elapsed_seconds - self.shrink_start_second
		return smooth_step(max(0.0, min(1.0, seconds_into_shrink / self.shrink_seconds)))

	def update(self, seconds):
		self.elapsed_seconds += seconds
		if not self.jabba_has_set_off and self.elapsed_seconds >= self.jabba_arrival_delay_seconds:
			self.jabba_has_set_off = True
			self.portrait.glide_center_to((self.jabba_stop_fraction_from_left, self.jabba_fraction_from_top),
			                              self.jabba_arrival_seconds, easing=ease_out_cubic)
		if not self.morph_has_started and self.elapsed_seconds >= self.morph_start_second:
			self._start_morph()
		if not self.speech_has_started and self.elapsed_seconds >= self.morph_end_second:
			self.speech_has_started = True
			self.jack_speech_bubble.start()
			self.year_flashes.start()
		self.portrait.horizontal_scale = 1.0 + (self.jack_shrunk_width_scale - 1.0) * self.shrink_progress
		if self.big_jack_revealed:
			self.big_jack_reveal_seconds += seconds
			self.big_jack.opacity = self.big_jack_opacity
			self.portrait.opacity = 1.0 - self.big_jack_opacity
		self.portrait.update(seconds)
		self.mos_logo.update(seconds)
		self.jack_speech_bubble.update(seconds)
		self.year_flashes.update(seconds)

	def _start_morph(self):
		self.morph_has_started = True
		self.portrait.crossfade_to(self.jack_stretched_to_jabba_width_picture, self.picture_crossfade_seconds)
		self.mos_logo.glide_center_to((self.logo_stop_fraction_from_left, self.jabba_fraction_from_top),
		                              self.morph_end_second - self.morph_start_second, easing=ease_out_cubic)

	def draw(self):
		if not self.jabba_has_set_off:
			return
		if self.portrait.opacity > 0.0:
			self.portrait.draw()
		if self.big_jack_revealed:
			self.big_jack.draw()
		self._draw_caption_under_portrait()
		if self.morph_has_started:
			self.mos_logo.draw()
		self._draw_speech_bubble_above_portrait()
		self.year_flashes.draw()

	def _draw_caption_under_portrait(self):
		portrait_center_x, portrait_center_y = self.portrait.world_center_point
		jack_moved_x, jack_moved_y = self._how_far_big_jack_moved_since_reveal()
		caption_center_y = (portrait_center_y - self.portrait.picture_height / 2 - self.caption_gap
		                    - self.caption.text_height / 2 + jack_moved_y)
		self.caption.draw_centered_at(portrait_center_x + jack_moved_x, caption_center_y, -self.screen_plane.camera_distance,
		                              self.caption_morph_progress)

	def _draw_speech_bubble_above_portrait(self):
		portrait_top_x, portrait_top_y = self.portrait.world_top_center_point
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.jack_speech_bubble.draw(portrait_top_x, portrait_top_y, -self.screen_plane.camera_distance)
		glPopMatrix()

	def destroy(self):
		self.jabba_picture.destroy()
		self.jack_stretched_to_jabba_width_picture.destroy()
		self.big_jack_picture.destroy()
		self.caption.destroy()
		self.mos_logo.destroy()
		self.jack_speech_bubble.release()
		self.year_flashes.destroy()
