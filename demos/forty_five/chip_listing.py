from OpenGL.GL import *

from lib.laser_line import smooth_step
from demos.forty_five.typed_label import TypedLabel


class ChipToPictureLine:

	def __init__(self, screen_plane, chip_animation, picture_surface, picture_point_in_picture_fractions, grow_seconds,
	             line_width_px):
		self.screen_plane = screen_plane
		self.chip_animation = chip_animation
		self.picture_surface = picture_surface
		self.picture_point_in_picture_fractions = picture_point_in_picture_fractions
		self.grow_seconds = grow_seconds
		self.line_width_px = line_width_px
		self.opacity = 1.0
		self.elapsed_seconds = None

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.grow_seconds

	def start(self):
		self.elapsed_seconds = 0.0
		self.opacity = 1.0

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def _end_points(self):
		chip_x, chip_y = self.screen_plane.world_point_from_screen_fractions(
			*self.chip_animation.bottom_center_screen_fractions())
		fraction_x, fraction_y = self.picture_point_in_picture_fractions
		picture = self.picture_surface.picture
		picture_x, picture_y = self.picture_surface.world_point_from_picture_pixel(fraction_x * picture.pixel_width,
		                                                                           fraction_y * picture.pixel_height)
		return (chip_x, chip_y), (picture_x, picture_y)

	def draw(self):
		if not self.started:
			return
		progress = smooth_step(min(1.0, self.elapsed_seconds / self.grow_seconds))
		(end_x, end_y), (start_x, start_y) = self._end_points()
		depth = -self.screen_plane.camera_distance
		glLineWidth(self.line_width_px)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(1.0, 1.0, 1.0, self.opacity)
		glBegin(GL_LINES)
		glVertex3f(start_x, start_y, depth)
		glVertex3f(start_x + (end_x - start_x) * progress, start_y + (end_y - start_y) * progress, depth)
		glEnd()
		glLineWidth(1.0)


class ChipListing:

	def __init__(self, screen_plane, header, chip_names, picture_surface, line_targets_in_picture_fractions):
		self.screen_plane = screen_plane
		self.picture_surface = picture_surface
		self.line_targets_in_picture_fractions = line_targets_in_picture_fractions
		self.text_line_height = 0.6
		self.text_line_gap = 0.3
		self.text_frames_per_letter = 4
		self.line_grow_seconds = 0.5
		self.line_width_px = 2.0
		self.centre_x = 0.0
		self.vertical_offset = 0.0
		self.labels = tuple(TypedLabel(text, self.text_line_height, frames_per_letter=self.text_frames_per_letter)
		                    for text in (header,) + chip_names)
		for label in self.labels:
			label.build()
		self.chip_lines = ()
		self.typing_index = 0
		self.typing = False
		self.finished = False

	@property
	def character_width(self):
		header_label = self.labels[0]
		return header_label.height * header_label.aspect / len(header_label.text)

	@property
	def top_y(self):
		line_step = self.text_line_height + self.text_line_gap
		return line_step * (len(self.labels) - 1) / 2 + self.text_line_height / 2 + self.vertical_offset

	def begin(self, chip_animations):
		self.chip_lines = tuple(
			ChipToPictureLine(self.screen_plane, chip_animation, self.picture_surface, target, self.line_grow_seconds,
			                  self.line_width_px)
			for chip_animation, target in zip(chip_animations, self.line_targets_in_picture_fractions))
		for label in self.labels:
			label.restart()
		self.typing_index = 0
		self.vertical_offset = 0.0
		self.typing = True
		self.finished = False

	def update(self, seconds):
		for chip_line in self.chip_lines:
			chip_line.update(seconds)
		if self.typing:
			self._advance_typing()

	def _advance_typing(self):
		label = self.labels[self.typing_index]
		label.update()
		if not label.finished:
			return
		chip_line = self.chip_lines[self.typing_index - 1] if self.typing_index > 0 else None
		if chip_line is not None and not chip_line.started:
			chip_line.start()
		if chip_line is not None and not chip_line.finished:
			return
		if self.typing_index + 1 < len(self.labels):
			self.typing_index += 1
		else:
			self.typing = False
			self.finished = True

	def fade_lines(self, opacity):
		for chip_line in self.chip_lines:
			chip_line.opacity = opacity

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_TEXTURE_2D)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		for chip_line in self.chip_lines:
			chip_line.draw()
		self._draw_labels()
		glPopMatrix()
		glPopAttrib()

	def _draw_labels(self):
		line_step = self.text_line_height + self.text_line_gap
		top_centre_y = line_step * (len(self.labels) - 1) / 2 + self.vertical_offset
		depth = -self.screen_plane.camera_distance
		for index, label in enumerate(self.labels):
			label.draw((self.centre_x, top_centre_y - index * line_step, depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))

	def destroy(self):
		for label in self.labels:
			label.destroy()
