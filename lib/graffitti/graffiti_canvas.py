from OpenGL.GL import *

from lib.graffitti.spray_shader import SprayShader


class GraffitiCanvas:

	def __init__(self, logical_width, logical_height, pixel_width):
		self.logical_width = logical_width
		self.logical_height = logical_height
		self.pixel_width = pixel_width
		self.pixel_height = round(pixel_width * logical_height / logical_width)
		self.shader = SprayShader()
		self.pieces = []
		self.texture = self._create_texture()
		self.framebuffer = self._create_framebuffer()

	@property
	def aspect_ratio(self):
		return self.logical_width / self.logical_height

	def _create_texture(self):
		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.pixel_width, self.pixel_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
		return texture

	def _create_framebuffer(self):
		framebuffer = glGenFramebuffers(1)
		glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
		if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
			raise RuntimeError("graffiti canvas framebuffer incomplete")
		glBindFramebuffer(GL_FRAMEBUFFER, 0)
		return framebuffer

	def add(self, *pieces):
		self.pieces.extend(pieces)

	def render(self, seconds):
		glPushAttrib(GL_VIEWPORT_BIT | GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
		glViewport(0, 0, self.pixel_width, self.pixel_height)
		glClearColor(0.0, 0.0, 0.0, 0.0)
		glClear(GL_COLOR_BUFFER_BIT)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0, self.logical_width, self.logical_height, 0, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.shader.use()
		for piece in self.pieces:
			piece.draw(seconds, self.shader)
		self.shader.release()
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glBindFramebuffer(GL_FRAMEBUFFER, 0)
		glPopAttrib()
