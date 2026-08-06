"""IBM PC 45th-anniversary demo - pygame + OpenGL front-end.

Run from the DEMOS project root so the relative resource paths resolve:

    python -m demos.pc45.main

Owns the window and the OpenGL context, then plays a sequence of stages. Stage1
is the DOS-boot / zoom-out / date-counter / fireworks anniversary; when it
finishes it is destroyed and Stage2 - a 3D relief of Don Estridge's photo -
takes over. ESC / window-close quits.
"""

import os

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, FULLSCREEN, MOUSEBUTTONDOWN
from OpenGL.GL import glClearColor, glClear, glMatrixMode, GL_PROJECTION, GL_MODELVIEW, GL_COLOR_BUFFER_BIT
from OpenGL.GLU import gluPerspective

from lib import Globals

try:
	from stage1 import Stage1
except ModuleNotFoundError:
	from demos.pc45.stage1 import Stage1

try:
	from stage2 import Stage2
except ModuleNotFoundError:
	from demos.pc45.stage2 import Stage2

try:
	from stage3 import Stage3
except ModuleNotFoundError:
	from demos.pc45.stage3 import Stage3

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GlDemo:

	WIN_W, WIN_H = 1280, 800
	RES_PATH = os.path.join(_ROOT, "demos", "pc45", "resources")
	FOV = 45.0
	FPS = 60

	def __init__(self, windowed=False, triggered=False):
		pygame.init()
		pygame.mixer.init()
		flags = DOUBLEBUF | OPENGL
		if not windowed:
			flags |= FULLSCREEN
		pygame.display.set_mode((self.WIN_W, self.WIN_H), flags)
		pygame.display.set_caption("45 years of IBM-PC")
		pygame.mouse.set_pos((self.WIN_W - 1, self.WIN_H // 2))

		glClearColor(0.0, 0.0, 0.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.FOV, self.WIN_W / self.WIN_H, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)

		self.clock = pygame.time.Clock()
		self.running = False
		self.paused = triggered
		self._stages = [Stage1, Stage2, Stage3]
		self._index = 0
		self.stage = self._make_stage(0)
		if self.paused:
			pygame.mixer.music.pause()

	def _make_stage(self, index):
		return self._stages[index](self.WIN_W, self.WIN_H, self.RES_PATH, self.FOV)

	def _advance(self):
		self.stage.destroy()
		self._index += 1
		if self._index < len(self._stages):
			self.stage = self._make_stage(self._index)
		else:
			self.running = False
			print(Globals.get_duration())
			print("BYE !")

	def _process_events(self):
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				self.running = False
			elif event.type == MOUSEBUTTONDOWN and self.paused:
				self.paused = False
				pygame.mixer.music.unpause()

	def run(self):
		self.running = True
		while self.running:
			self._process_events()
			if self.paused:
				glClear(GL_COLOR_BUFFER_BIT)
			else:
				self.stage.render()
				if self.stage.done:
					self._advance()
			pygame.display.flip()
			self.clock.tick(self.FPS)
		pygame.quit()


if __name__ == "__main__":
	GlDemo().run()
