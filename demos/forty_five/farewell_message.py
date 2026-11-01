from OpenGL.GL import *

from demos.forty_five.typed_label import TypedLabel

THANKS_LINE = "Thanks for watching !"
CIGARS_WARNING_LINE = "Don't smoke cigars !"
RETRO_WARNING_LINE = "Don't destroy retro computers !!!"
CELEBRATION_LINE = "Instead, celebrate"
ANNIVERSARY_LINE = "the 45th anniversary of C64"


class FarewellMessage:

	def __init__(self, screen_plane, left_neighbour_right_x):
		self.screen_plane = screen_plane
		self.white_rgb = (1.0, 1.0, 1.0)
		self.red_rgb = (230 / 255, 40 / 255, 40 / 255)
		self.frames_per_letter = 3
		self.wanted_line_height = 0.55
		self.line_spacing_in_line_heights = 1.6
		self.gap_from_left_neighbour = 0.8
		self.right_margin = 0.5
		self.top_fraction_from_top = 0.62
		self.blink_seconds = 0.5
		self.hold_seconds_after_typing = 3.0
		self.text_left_x = left_neighbour_right_x + self.gap_from_left_neighbour
		self.thanks_label = self._label(THANKS_LINE, self.white_rgb)
		self.cigars_warning_label = self._label(CIGARS_WARNING_LINE, self.red_rgb)
		self.retro_warning_label = self._label(RETRO_WARNING_LINE, self.red_rgb)
		self.celebration_label = self._label(CELEBRATION_LINE, self.white_rgb)
		self.anniversary_label = self._label(ANNIVERSARY_LINE, self.white_rgb)
		self.labels = (self.thanks_label, self.cigars_warning_label, self.retro_warning_label, self.celebration_label,
		               self.anniversary_label)
		self.blinking_labels = (self.cigars_warning_label, self.retro_warning_label)
		self._fit_lines_into_width()
		self.typing_index = 0
		self.seconds_since_typed = 0.0
		self.phase = "idle"

	def _label(self, text, tint_rgb):
		label = TypedLabel(text, self.wanted_line_height, frames_per_letter=self.frames_per_letter)
		label.build()
		label.tint_rgb = tint_rgb
		return label

	def _fit_lines_into_width(self):
		available_width = self.screen_plane.visible_width / 2 - self.right_margin - self.text_left_x
		widest_aspect = max(label.aspect for label in self.labels)
		line_height = min(self.wanted_line_height, available_width / widest_aspect)
		for label in self.labels:
			label.height = line_height

	@property
	def started(self):
		return self.phase != "idle"

	@property
	def done(self):
		return self.phase == "holding" and self.seconds_since_typed >= self.hold_seconds_after_typing

	def begin(self):
		for label in self.labels:
			label.restart()
		self.typing_index = 0
		self.seconds_since_typed = 0.0
		self.phase = "typing"

	def update(self, seconds):
		if self.phase == "typing":
			self._advance_typing()
		elif self.phase == "holding":
			self.seconds_since_typed += seconds

	def _advance_typing(self):
		label = self.labels[self.typing_index]
		label.update()
		if not label.finished:
			return
		if self.typing_index + 1 < len(self.labels):
			self.typing_index += 1
		else:
			self.phase = "holding"

	def _shows(self, label):
		if self.phase != "holding" or label not in self.blinking_labels:
			return True
		blink_index = int(self.seconds_since_typed / self.blink_seconds) % len(self.blinking_labels)
		return self.blinking_labels[blink_index] is label

	def draw_overlay(self):
		if not self.started:
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		depth = -self.screen_plane.camera_distance
		top_line_y = (0.5 - self.top_fraction_from_top) * self.screen_plane.visible_height
		for index, label in enumerate(self.labels):
			if not self._shows(label):
				continue
			line_y = top_line_y - index * label.height * self.line_spacing_in_line_heights
			centre_x = self.text_left_x + label.height * label.aspect / 2
			label.draw((centre_x, line_y, depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		for label in self.labels:
			label.destroy()
