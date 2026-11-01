import pygame
from OpenGL.GL import *

from demos.forty_five.geometry import upload_texture
from demos.forty_five.typed_label import TypedLabel
from lib.laser_line import smooth_step
from lib.typer import FONT_PATH

ANNOUNCEMENT_LINES = (
	"Ladies and gentlemen!",
	"It's my honor to present to you...",
	"the one and only...",
)
MAKE_CAPTION = "COMMODORE"
MODEL_CAPTION = "64"


class ZoomingCaption:

	def __init__(self, screen_plane, text):
		self.screen_plane = screen_plane
		self.text = text
		self.font_px = 160
		self.font_rgb = (255, 255, 255)
		self.opacity = 0.7
		self.zoom_seconds = 3.0
		self.hold_seconds = 3.0
		self.start_width_in_screen_widths = 0.05
		self.final_width_in_screen_widths = 0.85
		self.elapsed_seconds = 0.0
		self.started = False
		self._texture = None

	def build(self):
		pygame.font.init()
		font = pygame.font.Font(FONT_PATH, self.font_px)
		surface = font.render(self.text, True, self.font_rgb)
		self.aspect = surface.get_width() / surface.get_height()
		self._texture = upload_texture(surface)

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.zoom_seconds + self.hold_seconds

	def begin(self):
		self.elapsed_seconds = 0.0
		self.started = True

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def width(self):
		progress = smooth_step(min(1.0, self.elapsed_seconds / self.zoom_seconds))
		width_in_screen_widths = (self.start_width_in_screen_widths
		                          + (self.final_width_in_screen_widths - self.start_width_in_screen_widths) * progress)
		return width_in_screen_widths * self.screen_plane.visible_width

	def height(self):
		return self.width() / self.aspect

	def draw(self, centre_x, centre_y, scale):
		if not self.started:
			return
		half_width = self.width() * scale / 2
		half_height = self.height() * scale / 2
		depth = -self.screen_plane.camera_distance
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._texture)
		glColor4f(1.0, 1.0, 1.0, self.opacity)
		glBegin(GL_QUADS)
		for (s, t), (across, along) in (((0, 0), (-1, -1)), ((1, 0), (1, -1)), ((1, 1), (1, 1)), ((0, 1), (-1, 1))):
			glTexCoord2f(s, t)
			glVertex3f(centre_x + across * half_width, centre_y + along * half_height, depth)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		if self._texture:
			glDeleteTextures([self._texture])
			self._texture = None


class GrandPresentation:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.line_height = 0.6
		self.frames_per_letter = 4
		self.pause_seconds_between_lines = 1.0
		self.line_margin_from_bottom = 0.8
		self.announcement_labels = tuple(TypedLabel(line, self.line_height, frames_per_letter=self.frames_per_letter)
		                                 for line in ANNOUNCEMENT_LINES)
		for label in self.announcement_labels:
			label.build()
		self.model_to_make_height_ratio = 1.6
		self.gap_in_make_heights = 0.15
		self.captions_centre_y_in_screen_heights = 0.05
		self.make_caption = ZoomingCaption(screen_plane, MAKE_CAPTION)
		self.make_caption.build()
		self.model_caption = ZoomingCaption(screen_plane, MODEL_CAPTION)
		self.model_caption.build()
		for width_attribute in ("start_width_in_screen_widths", "final_width_in_screen_widths"):
			make_width = getattr(self.make_caption, width_attribute)
			setattr(self.model_caption, width_attribute, make_width * self.model_to_make_height_ratio
			        * self.model_caption.aspect / self.make_caption.aspect)
		self.captions = (self.make_caption, self.model_caption)
		self.retreat_seconds = 2.0
		self.retreated_scale = 0.25
		self.corner_margin = 0.6
		self.retreat_elapsed_seconds = 0.0
		self.line_index = 0
		self.pause_seconds = 0.0
		self.phase = "idle"

	@property
	def done(self):
		return self.phase == "caption" and all(caption.finished for caption in self.captions)

	@property
	def _current_label(self):
		return self.announcement_labels[self.line_index]

	def begin(self):
		for label in self.announcement_labels:
			label.restart()
		self.line_index = 0
		self.pause_seconds = 0.0
		self.phase = "typing"

	def update(self, seconds):
		if self.phase == "typing":
			self._advance_typing()
		elif self.phase == "pausing":
			self.pause_seconds += seconds
			if self.pause_seconds >= self.pause_seconds_between_lines:
				self.line_index += 1
				self.phase = "typing"
		elif self.phase == "caption":
			for caption in self.captions:
				caption.update(seconds)
		elif self.phase == "retreat":
			self.retreat_elapsed_seconds += seconds

	def begin_retreat(self):
		self.retreat_elapsed_seconds = 0.0
		self.phase = "retreat"

	def _retreat_progress(self):
		if self.phase != "retreat":
			return 0.0
		return smooth_step(min(1.0, self.retreat_elapsed_seconds / self.retreat_seconds))

	def _advance_typing(self):
		self._current_label.update()
		if not self._current_label.finished:
			return
		if self.line_index + 1 < len(self.announcement_labels):
			self.pause_seconds = 0.0
			self.phase = "pausing"
		else:
			for caption in self.captions:
				caption.begin()
			self.phase = "caption"

	def draw_overlay(self):
		if self.phase == "idle":
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self._draw_captions()
		if self.phase != "retreat":
			line_y = -self.screen_plane.visible_height / 2 + self.line_margin_from_bottom
			self._current_label.draw((0.0, line_y, -self.screen_plane.camera_distance), (1.0, 0.0, 0.0),
			                         (0.0, 1.0, 0.0))
		glPopMatrix()
		glPopAttrib()

	def _draw_captions(self):
		retreat_progress = self._retreat_progress()
		scale = 1.0 + (self.retreated_scale - 1.0) * retreat_progress
		make_height, model_height = self.make_caption.height() * scale, self.model_caption.height() * scale
		gap = self.gap_in_make_heights * make_height
		stack_height = make_height + gap + model_height
		stack_width = max(self.make_caption.width(), self.model_caption.width()) * scale
		centred_stack_y = self.captions_centre_y_in_screen_heights * self.screen_plane.visible_height
		corner_stack_x = -self.screen_plane.visible_width / 2 + self.corner_margin + stack_width / 2
		corner_stack_y = -self.screen_plane.visible_height / 2 + self.corner_margin + stack_height / 2
		stack_centre_x = corner_stack_x * retreat_progress
		stack_centre_y = centred_stack_y + (corner_stack_y - centred_stack_y) * retreat_progress
		self.make_caption.draw(stack_centre_x, stack_centre_y + stack_height / 2 - make_height / 2, scale)
		self.model_caption.draw(stack_centre_x, stack_centre_y - stack_height / 2 + model_height / 2, scale)

	def destroy(self):
		for label in self.announcement_labels:
			label.destroy()
		for caption in self.captions:
			caption.destroy()
