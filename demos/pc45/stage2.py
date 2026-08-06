import math
import os

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

try:
	from audio import AudioController
except ModuleNotFoundError:
	from demos.pc45.audio import AudioController

try:
	from base_stage import BaseStage
except ModuleNotFoundError:
	from demos.pc45.base_stage import BaseStage

try:
	from effects.portrait import ExtrudedPhoto
except ModuleNotFoundError:
	from demos.pc45.effects.portrait import ExtrudedPhoto

try:
	from team_cube import TeamCube
except ModuleNotFoundError:
	from demos.pc45.team_cube import TeamCube

try:
	from team_slides import TeamSlides
except ModuleNotFoundError:
	from demos.pc45.team_slides import TeamSlides

try:
	from stage2textwall import Textwall
except ModuleNotFoundError:
	from demos.pc45.stage2textwall import Textwall

try:
	from march_on_with_ibm import MarchOnWithIBM
except ModuleNotFoundError:
	from demos.pc45.march_on_with_ibm import MarchOnWithIBM

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Stage2(BaseStage):

	FPS = 60
	PORTRAIT_DEPTH_PX = 30
	HALF_HEIGHT = 0.9
	CAM_Z = -3.0
	YAW = 24.0
	YAW_SPEED = 0.5

	LYRIC_FONT = os.path.join(_ROOT, "lib", "resources", "Mx437_IBM_MDA.ttf")
	LYRIC_PX = 28
	LYRIC_COLOR = (87, 255, 163)
	LYRIC_MARGIN = 24

	def __init__(self, win_w, win_h, res_path, fov):
		super().__init__(win_w, win_h, res_path, fov)
		self.tune = "MarchOnWithIBM.mp3"
		self.tune_seconds = 76
		self.portrait_images = (
			("team/DonEstridge.png", "Don Estridge"),
			("team/mark-dean.png", "Mark Dean"),
			("team/DennisL.Moeller.png", "Dennis L. Moeller"),
			("team/wiliamLowe.png", "William Lowe"),
		)
		self.portrait_seconds = 3
		self.name_margin = 24
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)
		self.portraits = [ExtrudedPhoto(os.path.join(res_path, img), self.HALF_HEIGHT, self.PORTRAIT_DEPTH_PX)
		                  for img, name in self.portrait_images]
		self.audio = AudioController(self.res_path, self.tune)
		self.audio.start()
		self.font = pygame.font.Font(self.LYRIC_FONT, self.LYRIC_PX)
		self.name_texs = [self._texture_from_surface(self.font.render(name, True, (255, 255, 255)))
		                  for img, name in self.portrait_images]
		self.lyric_tex = self.make_texture()
		self._lyric_line = None
		self._lyric_w = 0
		self._lyric_h = 0
		self.ceo_image = "tjw.jpg"
		self.ceo_scale = 0.25
		self.ceo_line = "With T.J. Watson guiding us"
		self.ceo_margin = 30
		ceo = pygame.image.load(os.path.join(res_path, self.ceo_image))
		ceo = pygame.transform.smoothscale(
			ceo, (int(ceo.get_width() * self.ceo_scale), int(ceo.get_height() * self.ceo_scale)))
		self.ceo, self.ceo_w, self.ceo_h = self._texture_from_surface(ceo)
		self.cube = TeamCube(self.res_path, [img for img, name in self.portrait_images])
		self.cube_fraction = 0.15
		self.cube_margin = 20
		self.slides_start = len(self.portraits) * self.portrait_seconds
		screens = (
			("team/DonEstridge.png", Textwall.don_estridge, 2.0),
			("team/mark-dean.png", Textwall.mark_dean, 1.0),
			("team/DennisL.Moeller.png", Textwall.dennis_moeller, 2.0),
			("team/wiliamLowe.png", Textwall.william_lowe, 2.0),
			(None, Textwall.others, 3.0),
		)
		self.slideshow = TeamSlides(self.res_path, self.win_w, self.win_h,
		                            self.tune_seconds - self.slides_start, screens,
		                            travel_image="ISAslot.png", travel_slides=(1, 2))

	def render(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, self.CAM_Z)
		angle = self.YAW * math.sin(self.frame / self.FPS * self.YAW_SPEED)
		glRotatef(angle, 0.0, 1.0, 0.0)
		i = int(self.frame / self.FPS / self.portrait_seconds)
		if i < len(self.portraits):
			self.portraits[i].draw()
		self._update_lyric(MarchOnWithIBM.line_at(self._elapsed()))
		self._draw_ceo()
		self._draw_lyric()
		if i < len(self.portraits):
			self._draw_name(i)
		else:
			self.slideshow.draw(self.frame / self.FPS - self.slides_start)
			self._draw_cube()
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

	def _blit(self, tex, x, y, w, h):
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
		glBindTexture(GL_TEXTURE_2D, tex)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex2f(x, y)
		glTexCoord2f(1.0, 0.0); glVertex2f(x + w, y)
		glTexCoord2f(1.0, 1.0); glVertex2f(x + w, y + h)
		glTexCoord2f(0.0, 1.0); glVertex2f(x, y + h)
		glEnd()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)

	def _draw_lyric(self):
		if not self._lyric_line:
			return
		x = (self.win_w - self._lyric_w) / 2.0
		self._blit(self.lyric_tex, x, self.LYRIC_MARGIN, self._lyric_w, self._lyric_h)

	def _draw_ceo(self):
		if self._lyric_line != self.ceo_line:
			return
		x = self.win_w - self.ceo_w - self.ceo_margin
		self._blit(self.ceo, x, self.ceo_margin, self.ceo_w, self.ceo_h)

	def _draw_name(self, i):
		tex, w, h = self.name_texs[i]
		self._blit(tex, (self.win_w - w) / 2.0, self.win_h - h - self.name_margin, w, h)

	def _texture_from_surface(self, surface):
		tex = self.make_texture()
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(surface, "RGBA", True))
		return tex, surface.get_width(), surface.get_height()

	def _draw_cube(self):
		rw = int(self.win_w * self.cube_fraction)
		rh = int(self.win_h * self.cube_fraction)
		glViewport(self.cube_margin, self.cube_margin, rw, rh)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		gluPerspective(45.0, rw / rh, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_BLEND)
		glTranslatef(0.0, 0.0, -4.5)
		glRotatef(18.0, 1.0, 0.0, 0.0)
		self.cube.update()
		self.cube.draw()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glViewport(0, 0, self.win_w, self.win_h)

	@property
	def done(self):
		return self.frame / self.FPS >= self.tune_seconds

	def destroy(self):
		for p in self.portraits:
			p.destroy()
		self.cube.destroy()
		self.slideshow.destroy()
		glDeleteTextures([self.ceo, self.lyric_tex, *[t for t, _, _ in self.name_texs]])
