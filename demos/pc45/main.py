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
from OpenGL.GL import glClearColor, glMatrixMode, GL_PROJECTION, GL_MODELVIEW
from OpenGL.GLU import gluPerspective

from lib import Globals
from lib.pygame_demo import PygameDemo

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


class GlDemo(PygameDemo):

	RES_PATH = os.path.join(_ROOT, "demos", "pc45", "resources")
	FOV = 45.0

	def __init__(self, windowed=False, triggered=False):
		super().__init__(1280, 800, "45 years of IBM-PC", fps=60,
		                 windowed=windowed, triggered=triggered)

	def setup(self):
		pygame.mixer.init()
		pygame.mouse.set_pos((self.width - 1, self.height // 2))

		glClearColor(0.0, 0.0, 0.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.FOV, self.width / self.height, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)

		self._stages = (Stage1, Stage2, Stage3)
		self._index = 0
		self.stage = self._make_stage(0)

	def on_pause(self):
		pygame.mixer.music.pause()

	def on_start(self):
		pygame.mixer.music.unpause()

	def _make_stage(self, index):
		return self._stages[index](self.width, self.height, self.RES_PATH, self.FOV)

	def _advance(self):
		self.stage.destroy()
		self._index += 1
		if self._index < len(self._stages):
			self.stage = self._make_stage(self._index)
		else:
			self.running = False
			print(Globals.get_duration())
			print("BYE !")

	def step(self):
		self.stage.render()
		if self.stage.done:
			self._advance()


if __name__ == "__main__":
	GlDemo().run()
