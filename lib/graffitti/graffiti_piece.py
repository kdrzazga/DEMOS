from OpenGL.GL import *

from lib.graffitti.keyframes import Keyframes, linear


class GraffitiPiece:

	def __init__(self, spray_texture, position_track, scale=1.0):
		self.spray_texture = spray_texture
		self.position_track = position_track
		self.scale = Keyframes(scale)
		self.progress = Keyframes(0.0)
		self.opacity = Keyframes(1.0)

	def spray(self, start_seconds, duration_seconds):
		self.progress.animate(start_seconds, duration_seconds, 1.0, linear)
		return self

	def unspray(self, start_seconds, duration_seconds):
		self.progress.animate(start_seconds, duration_seconds, 0.0, linear)
		return self

	def fade_out(self, start_seconds, duration_seconds):
		self.opacity.animate(start_seconds, duration_seconds, 0.0)
		return self

	def draw(self, seconds, shader):
		progress = self.progress.value(seconds)
		opacity = self.opacity.value(seconds)
		if progress <= 0.0 or opacity <= 0.0:
			return
		center_x, center_y = self.position_track.value(seconds)
		scale = self.scale.value(seconds)
		half_width = self.spray_texture.width * scale / 2
		half_height = self.spray_texture.height * scale / 2
		left, right = center_x - half_width, center_x + half_width
		top, bottom = center_y - half_height, center_y + half_height
		self.spray_texture.bind()
		shader.apply(progress, opacity)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0)
		glVertex2f(left, top)
		glTexCoord2f(1.0, 0.0)
		glVertex2f(right, top)
		glTexCoord2f(1.0, 1.0)
		glVertex2f(right, bottom)
		glTexCoord2f(0.0, 1.0)
		glVertex2f(left, bottom)
		glEnd()
