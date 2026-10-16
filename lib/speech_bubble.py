import os

import pygame
from OpenGL.GL import *


class SpeechBubble:

	def __init__(self, mp3_file, text_file, size=10):
		self.bubble_pic = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "speech-bubble.png")
		self.mp3_file = mp3_file
		self.font_size = size
		self.lines = self._read_lines(text_file)
		self.font_scale = 2.0
		self.text_width_share = 0.7
		self.text_height_share = 0.55
		self.texture_scale = 4
		self.units_per_pixel = 0.01
		self.offset = (0.5, 0.4, 0.0)
		self.text_color = (20, 20, 20)
		self.text_center = (0.53, 0.45)
		self.line_spacing = 1.15
		self.width, self.height = self._bubble_size()
		self.sound = None
		self.channel = None
		self.elapsed = 0.0
		self.length = 0.0
		self.started = False
		self.visible = False
		self.texture = 0
		self.picture = None
		self.font = None

	@staticmethod
	def _read_lines(text_file):
		with open(text_file, encoding="utf-8") as text:
			lines = [line.strip() for line in text.read().splitlines()]
		return [line for line in lines if line] or [""]

	def _font(self, scale):
		pygame.font.init()
		return pygame.font.Font(None, int(self.font_size * self.font_scale * scale))

	def _bubble_size(self):
		font = self._font(1)
		text_width = max(font.size(line)[0] for line in self.lines)
		text_height = font.get_linesize() * self.line_spacing * len(self.lines)
		width = text_width / self.text_width_share
		height = max(width * self._picture_aspect(), text_height / self.text_height_share)
		return width, height

	def _picture_aspect(self):
		width, height = pygame.image.load(self.bubble_pic).get_size()
		return height / width

	@property
	def speaking(self):
		return self.started and self.elapsed < self.length

	def _load(self):
		if self.sound is None:
			if not pygame.mixer.get_init():
				pygame.mixer.init()
			self.sound = pygame.mixer.Sound(self.mp3_file)
			self.length = self.sound.get_length()

	@property
	def duration(self):
		self._load()
		return self.length

	def start(self):
		self._load()
		self.channel = self.sound.play()
		self.elapsed = 0.0
		self.started = True
		self.visible = True

	def stop(self):
		if self.channel:
			self.channel.stop()
		self.visible = False

	def update(self, seconds):
		if not self.started:
			return
		self.elapsed += seconds
		if self.elapsed >= self.length:
			self.visible = False

	def _render_surface(self):
		scale = self.texture_scale
		width, height = int(self.width * scale), int(self.height * scale)
		if self.picture is None:
			self.picture = pygame.transform.smoothscale(pygame.image.load(self.bubble_pic).convert_alpha(), (width, height))
			self.font = self._font(scale)
		surface = self.picture.copy()
		line_height = self.font.get_linesize() * self.line_spacing
		top = height * self.text_center[1] - line_height * len(self.lines) / 2.0
		for index, line in enumerate(self.lines):
			left = width * self.text_center[0] - self.font.size(line)[0] / 2.0
			surface.blit(self.font.render(line, True, self.text_color), (left, top + index * line_height))
		return surface

	def _upload(self, surface):
		width, height = surface.get_size()
		pixels = pygame.image.tobytes(surface, "RGBA", True)
		if not self.texture:
			self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
		glBindTexture(GL_TEXTURE_2D, 0)

	def _refresh_texture(self):
		if not self.texture:
			self._upload(self._render_surface())

	def draw(self, x, y, z, yaw=0.0, pitch=0.0):
		if not self.visible:
			return
		self._refresh_texture()
		half_width = self.width * self.units_per_pixel / 2.0
		half_height = self.height * self.units_per_pixel / 2.0
		glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT | GL_TEXTURE_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_CULL_FACE)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_ALPHA_TEST)
		glAlphaFunc(GL_GREATER, 0.05)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glPushMatrix()
		glTranslatef(x, y, z)
		glRotatef(yaw, 0.0, 1.0, 0.0)
		glRotatef(pitch, 1.0, 0.0, 0.0)
		offset_x, offset_y, offset_z = self.offset
		glTranslatef(offset_x + half_width, offset_y + half_height, offset_z)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0)
		glVertex3f(-half_width, -half_height, 0.0)
		glTexCoord2f(1.0, 0.0)
		glVertex3f(half_width, -half_height, 0.0)
		glTexCoord2f(1.0, 1.0)
		glVertex3f(half_width, half_height, 0.0)
		glTexCoord2f(0.0, 1.0)
		glVertex3f(-half_width, half_height, 0.0)
		glEnd()
		glPopMatrix()
		glBindTexture(GL_TEXTURE_2D, 0)
		glPopAttrib()

	def draw_beside(self, part):
		self.draw(part.x, part.y, part.z, part.yaw, part.pitch)

	def release(self):
		if self.texture:
			glDeleteTextures([self.texture])
			self.texture = 0
