import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, K_ESCAPE, KEYDOWN, OPENGL, QUIT
from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GL_DEPTH_TEST, GL_FRONT_AND_BACK, GL_LIGHT0, GL_LIGHTING, GL_NORMALIZE,
	glColorMaterial, glEnable, glViewport,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.retrosfera10.phases.common import Camera, Handover
from demos.retrosfera10.phases.main_hall import MainHallPhase


class MainHallTestApp:
	def __init__(self, width=1280, height=800, fps=60):
		self.width = width
		self.height = height
		self.fps = fps
		self.running = True

	def setup_gl(self):
		glViewport(0, 0, self.width, self.height)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glEnable(GL_NORMALIZE)

	def run(self):
		pygame.init()
		pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
		pygame.display.set_caption("Main hall test - ESC quit")
		self.setup_gl()
		phase = MainHallPhase(Camera(self.width, self.height))
		phase.begin(Handover(None, 1.0, 0.0))
		clock = pygame.time.Clock()
		while self.running:
			for event in pygame.event.get():
				if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
					self.running = False
			phase.update(clock.tick(self.fps) / 1000.0)
			phase.render()
			pygame.display.flip()
		phase.hall.release()
		pygame.quit()


if __name__ == "__main__":
	MainHallTestApp().run()
