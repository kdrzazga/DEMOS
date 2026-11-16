from OpenGL.GL import *


class SolidTexture:

	def __init__(self):
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, bytes(4))

	def fill(self, color, opacity):
		premultiplied_pixel = bytes(round(channel * opacity * 255) for channel in (*color, 1.0))
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, premultiplied_pixel)
