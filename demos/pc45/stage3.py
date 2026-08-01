import os

import pygame
from OpenGL.GL import *

try:
	from base_stage import BaseStage
except ModuleNotFoundError:
	from demos.pc45.base_stage import BaseStage


class Stage3(BaseStage):

	FPS = 60

	def __init__(self, win_w, win_h, res_path, fov):
		super().__init__(win_w, win_h, res_path, fov)
		self.tunes = (("summary/summary.mp3", 30), ("summary/dominance.mp3", 3))
		self._index = 0
		self._tune_start = 0
		self.bg_image = "summary/HQ.jpg"
		bg = pygame.image.load(os.path.join(res_path, self.bg_image))
		self.bg_w, self.bg_h = bg.get_size()
		self.bg = self.make_texture()
		glBindTexture(GL_TEXTURE_2D, self.bg)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.bg_w, self.bg_h, 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(bg, "RGBA", True))
		glClearColor(0.0, 0.0, 0.0, 1.0)
		self._play(self.tunes[0][0])

	def _play(self, tune):
		try:
			pygame.mixer.music.load(os.path.join(self.res_path, tune))
			pygame.mixer.music.play()
		except pygame.error as exc:
			print("audio unavailable:", exc)

	def _draw_background(self):
		scale = max(self.win_w / self.bg_w, self.win_h / self.bg_h)
		sw = self.bg_w * scale
		sh = self.bg_h * scale
		x0 = (self.win_w - sw) / 2.0
		y0 = (self.win_h - sh) / 2.0
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_BLEND)
		glEnable(GL_TEXTURE_2D)
		glColor3f(1.0, 1.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0.0, self.win_w, 0.0, self.win_h, -1.0, 1.0)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glBindTexture(GL_TEXTURE_2D, self.bg)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex2f(x0, y0)
		glTexCoord2f(1.0, 0.0); glVertex2f(x0 + sw, y0)
		glTexCoord2f(1.0, 1.0); glVertex2f(x0 + sw, y0 + sh)
		glTexCoord2f(0.0, 1.0); glVertex2f(x0, y0 + sh)
		glEnd()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)

	def render(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self._draw_background()
		if self._index < len(self.tunes):
			elapsed = (self.frame - self._tune_start) / self.FPS
			if elapsed >= self.tunes[self._index][1]:
				self._index += 1
				self._tune_start = self.frame
				if self._index < len(self.tunes):
					self._play(self.tunes[self._index][0])
		self.frame += 1

	@property
	def done(self):
		return self._index >= len(self.tunes)

	def destroy(self):
		pygame.mixer.music.stop()
		glDeleteTextures([self.bg])
