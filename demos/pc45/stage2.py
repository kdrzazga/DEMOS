import math
import os

import pygame
from OpenGL.GL import *

try:
	from audio import AudioController
except ModuleNotFoundError:
	from demos.pc45.audio import AudioController

try:
	from base_stage import BaseStage
except ModuleNotFoundError:
	from demos.pc45.base_stage import BaseStage

try:
	from effects.portrait import ExtrudedPhoto, FlatImage
except ModuleNotFoundError:
	from demos.pc45.effects.portrait import ExtrudedPhoto, FlatImage

try:
	from march_on_with_ibm import MarchOnWithIBM
except ModuleNotFoundError:
	from demos.pc45.march_on_with_ibm import MarchOnWithIBM

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Stage2(BaseStage):

	FPS = 60
	PORTRAIT_DEPTH_PX = 10
	HALF_HEIGHT = 0.9
	CAM_Z = -3.0
	YAW = 24.0
	YAW_SPEED = 0.5

	CEO_IMAGE = "tjw.jpg"
	CEO_HALF_HEIGHT = 0.55
	CEO_X = -1.25
	CEO_Y = 0.0

	LYRIC_FONT = os.path.join(_ROOT, "lib", "resources", "Mx437_IBM_MDA.ttf")
	LYRIC_PX = 28
	LYRIC_COLOR = (87, 255, 163)
	LYRIC_MARGIN = 24

	def __init__(self, win_w, win_h, res_path, fov):
		super().__init__(win_w, win_h, res_path, fov)
		self.tune = "MarchOnWithIBM.mp3"
		self.portrait_image = "team/DonEstridge.png"
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)
		self.portrait = ExtrudedPhoto(os.path.join(res_path, self.portrait_image),
		                              self.HALF_HEIGHT, self.PORTRAIT_DEPTH_PX)
		self.audio = AudioController(self.res_path, self.tune)
		self.audio.start()
		self.font = pygame.font.Font(self.LYRIC_FONT, self.LYRIC_PX)
		self.lyric_tex = self.make_texture()
		self._lyric_line = None
		self._lyric_w = 0
		self._lyric_h = 0
		self.ceo = FlatImage(os.path.join(res_path, self.CEO_IMAGE), self.CEO_HALF_HEIGHT)

	def render(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, self.CAM_Z)
		angle = self.YAW * math.sin(self.frame / self.FPS * self.YAW_SPEED)
		glRotatef(angle, 0.0, 1.0, 0.0)
		self.portrait.draw()
		glLoadIdentity()
		glTranslatef(self.CEO_X, self.CEO_Y, self.CAM_Z)
		self.ceo.draw()
		self._update_lyric(MarchOnWithIBM.line_at(self._elapsed()))
		self._draw_lyric()
		self.frame += 1

	def _elapsed(self):
		pos = pygame.mixer.music.get_pos()
		if pos < 0:
			return self.frame / self.FPS
		return pos / 1000.0

	def _update_lyric(self, line):
		if line == self._lyric_line:
			return
		self._lyric_line = line
		if not line:
			return
		surface = self.font.render(line, True, self.LYRIC_COLOR)
		self._lyric_w, self._lyric_h = surface.get_size()
		data = pygame.image.tostring(surface, "RGBA", True)
		glBindTexture(GL_TEXTURE_2D, self.lyric_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self._lyric_w, self._lyric_h, 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, data)

	def _draw_lyric(self):
		if not self._lyric_line:
			return
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0.0, self.win_w, 0.0, self.win_h, -1.0, 1.0)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glEnable(GL_TEXTURE_2D)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBindTexture(GL_TEXTURE_2D, self.lyric_tex)
		x0 = (self.win_w - self._lyric_w) / 2.0
		x1 = x0 + self._lyric_w
		y0 = self.LYRIC_MARGIN
		y1 = y0 + self._lyric_h
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex2f(x0, y0)
		glTexCoord2f(1.0, 0.0); glVertex2f(x1, y0)
		glTexCoord2f(1.0, 1.0); glVertex2f(x1, y1)
		glTexCoord2f(0.0, 1.0); glVertex2f(x0, y1)
		glEnd()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)

	@property
	def done(self):
		return False

	def destroy(self):
		self.portrait.destroy()
		self.ceo.destroy()
