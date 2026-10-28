from OpenGL.GL import glColor4f

from lib.laser_line import smooth_step


class PictureCrossfade:

	def __init__(self, outgoing_picture, incoming_picture, fade_seconds):
		self.uses_laser_line = False
		self.outgoing_picture = outgoing_picture
		self.incoming_picture = incoming_picture
		self.fade_seconds = fade_seconds
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def incoming_picture_opacity(self):
		return smooth_step(min(1.0, self.elapsed_seconds / self.fade_seconds))

	@property
	def finished(self):
		return self.elapsed_seconds >= self.fade_seconds

	def draw_pictures(self, picture_width, picture_height):
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.outgoing_picture.draw_vertical_strip(0.0, 1.0, picture_width, picture_height)
		glColor4f(1.0, 1.0, 1.0, self.incoming_picture_opacity)
		self.incoming_picture.draw_vertical_strip(0.0, 1.0, picture_width, picture_height)
		glColor4f(1.0, 1.0, 1.0, 1.0)
