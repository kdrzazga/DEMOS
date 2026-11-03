import os

from OpenGL.GL import *

from lib.geometry import image_texture
from lib.typing_effect.typed_label import TypedLabel
from lib.laser_line import smooth_step

LIB_RESOURCES_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                       "lib", "resources")
KOMODA_AMIGA_PLUS_LOGO_PATH = os.path.join(LIB_RESOURCES_DIRECTORY, "K&Alogo.png")
DEMO_WORD = "Demo"
BROUGHT_BY_WORDS = "brought to you by"
CREDITS_LINE = "Code: KD, Music: AmigaManson."


class FinalGoodbye:

	def __init__(self, screen_plane, grand_presentation, farewell_message):
		self.screen_plane = screen_plane
		self.grand_presentation = grand_presentation
		self.farewell_message = farewell_message
		self.caption_fade_seconds = 1.0
		self.years_count_move_seconds = 1.5
		self.years_count_centre_fraction_from_top = 0.6
		self.words_line_height = 0.45
		self.gap_beside_years_count = 0.5
		self.frames_per_letter = 4
		self.logo_fade_seconds = 1.0
		self.logo_height_in_screen_heights = 0.2
		self.logo_centre_fraction_from_top = 0.78
		self.credits_line_height = 0.5
		self.credits_centre_fraction_from_top = 0.93
		self.hold_seconds_before_screen_fade = 2.0
		self.screen_fade_seconds = 1.5
		self.music_silent_seconds_before_end = 3.0
		self.music_fade_seconds = 2.0
		self.frames_per_second = 60
		self.demo_label = self._label(DEMO_WORD, self.words_line_height)
		self.brought_by_label = self._label(BROUGHT_BY_WORDS, self.words_line_height)
		self.credits_label = self._label(CREDITS_LINE, self.credits_line_height)
		self.logo_texture, self.logo_aspect = image_texture(KOMODA_AMIGA_PLUS_LOGO_PATH)
		self.years_count_start_centre = (0.0, 0.0)
		self.phase_elapsed_seconds = 0.0
		self.phase = "idle"

	def _label(self, text, height):
		label = TypedLabel(text, height, frames_per_letter=self.frames_per_letter)
		label.build()
		return label

	@property
	def started(self):
		return self.phase != "idle"

	@property
	def done(self):
		return self.phase == "screen_fade" and self.phase_elapsed_seconds >= self.screen_fade_seconds

	def _seconds_until_end(self):
		after_credits_seconds = self.hold_seconds_before_screen_fade + self.screen_fade_seconds
		if self.phase == "credits_typing":
			remaining_frames = len(self.credits_label.text) * self.frames_per_letter - self.credits_label.frame
			return remaining_frames / self.frames_per_second + after_credits_seconds
		if self.phase == "hold":
			return after_credits_seconds - self.phase_elapsed_seconds
		if self.phase == "screen_fade":
			return self.screen_fade_seconds - self.phase_elapsed_seconds
		return None

	@property
	def music_volume_factor(self):
		seconds_until_end = self._seconds_until_end()
		if seconds_until_end is None:
			return 1.0
		seconds_until_silence = seconds_until_end - self.music_silent_seconds_before_end
		return max(0.0, min(1.0, seconds_until_silence / self.music_fade_seconds))

	def begin(self):
		for label in (self.demo_label, self.brought_by_label, self.credits_label):
			label.restart()
		self.years_count_start_centre = self.grand_presentation.years_count_corner_centre
		self._enter("caption_fade")

	def _enter(self, phase):
		self.phase = phase
		self.phase_elapsed_seconds = 0.0

	def _phase_progress(self, seconds):
		return smooth_step(min(1.0, self.phase_elapsed_seconds / seconds))

	@property
	def _years_count_centre_target(self):
		return 0.0, (0.5 - self.years_count_centre_fraction_from_top) * self.screen_plane.visible_height

	def update(self, seconds):
		self.phase_elapsed_seconds += seconds
		if self.phase == "caption_fade":
			remaining_opacity = 1.0 - self._phase_progress(self.caption_fade_seconds)
			self.grand_presentation.dim_all_but_years_count(remaining_opacity)
			self.farewell_message.set_opacity(remaining_opacity)
			if self.phase_elapsed_seconds >= self.caption_fade_seconds:
				self._enter("years_count_move")
		elif self.phase == "years_count_move":
			self._move_years_count()
			if self.phase_elapsed_seconds >= self.years_count_move_seconds:
				self._enter("demo_typing")
		elif self.phase == "demo_typing":
			self._type_then_enter(self.demo_label, "brought_by_typing")
		elif self.phase == "brought_by_typing":
			self._type_then_enter(self.brought_by_label, "logo_fade")
		elif self.phase == "logo_fade" and self.phase_elapsed_seconds >= self.logo_fade_seconds:
			self._enter("credits_typing")
		elif self.phase == "credits_typing":
			self._type_then_enter(self.credits_label, "hold")
		elif self.phase == "hold" and self.phase_elapsed_seconds >= self.hold_seconds_before_screen_fade:
			self._enter("screen_fade")

	def _move_years_count(self):
		progress = self._phase_progress(self.years_count_move_seconds)
		self.grand_presentation.years_count_centre_override = tuple(
			start + (target - start) * progress
			for start, target in zip(self.years_count_start_centre, self._years_count_centre_target))

	def _type_then_enter(self, label, next_phase):
		label.update()
		if label.finished:
			self._enter(next_phase)

	def _has_reached(self, phase):
		order = ("caption_fade", "years_count_move", "demo_typing", "brought_by_typing", "logo_fade",
		         "credits_typing", "hold", "screen_fade")
		return self.started and order.index(self.phase) >= order.index(phase)

	def draw_overlay(self):
		if not self.started:
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self._draw_words_beside_years_count()
		if self._has_reached("logo_fade"):
			self._draw_logo()
		if self._has_reached("credits_typing"):
			credits_y = (0.5 - self.credits_centre_fraction_from_top) * self.screen_plane.visible_height
			self.credits_label.draw((0.0, credits_y, self._depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
		if self.phase == "screen_fade":
			self._draw_black_veil(self._phase_progress(self.screen_fade_seconds))
		glPopMatrix()
		glPopAttrib()

	@property
	def _depth(self):
		return -self.screen_plane.camera_distance

	def _draw_words_beside_years_count(self):
		if not self._has_reached("demo_typing"):
			return
		centre_x, centre_y = self._years_count_centre_target
		years_count_half_width = self.grand_presentation.years_count_width / 2
		demo_width = self.demo_label.height * self.demo_label.aspect
		brought_by_width = self.brought_by_label.height * self.brought_by_label.aspect
		demo_x = centre_x - years_count_half_width - self.gap_beside_years_count - demo_width / 2
		brought_by_x = centre_x + years_count_half_width + self.gap_beside_years_count + brought_by_width / 2
		self.demo_label.draw((demo_x, centre_y, self._depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
		self.brought_by_label.draw((brought_by_x, centre_y, self._depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))

	def _draw_logo(self):
		opacity = self._phase_progress(self.logo_fade_seconds) if self.phase == "logo_fade" else 1.0
		half_height = self.logo_height_in_screen_heights * self.screen_plane.visible_height / 2
		half_width = half_height * self.logo_aspect
		centre_y = (0.5 - self.logo_centre_fraction_from_top) * self.screen_plane.visible_height
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.logo_texture)
		glColor4f(1.0, 1.0, 1.0, opacity)
		glBegin(GL_QUADS)
		for (s, t), (across, along) in (((0, 0), (-1, -1)), ((1, 0), (1, -1)), ((1, 1), (1, 1)), ((0, 1), (-1, 1))):
			glTexCoord2f(s, t)
			glVertex3f(across * half_width*1.1, centre_y + along * half_height, self._depth)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def _draw_black_veil(self, darkness):
		half_width, half_height = self.screen_plane.visible_width, self.screen_plane.visible_height
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(0.0, 0.0, 0.0, darkness)
		glBegin(GL_QUADS)
		for across, along in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
			glVertex3f(across * half_width, along * half_height, self._depth)
		glEnd()

	def destroy(self):
		for label in (self.demo_label, self.brought_by_label, self.credits_label):
			label.destroy()
		if self.logo_texture:
			glDeleteTextures([self.logo_texture])
			self.logo_texture = None
