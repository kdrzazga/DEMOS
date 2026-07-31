"""Standalone demo of a single Firework (pygame + OpenGL).

    python -m demos.pc45.test.firework_test

Watch the shaft climb at 135 degrees, burst into 75 sparks, and fade to black.
The firework relaunches when it finishes. ESC / window-close quits.
"""

import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import (
	glClear, glClearColor, glEnable, glLoadIdentity, glMatrixMode, glTranslatef,
	GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_BLEND, GL_PROJECTION, GL_MODELVIEW,
)
from OpenGL.GLU import gluPerspective

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__))))))

from demos.pc45.effects.fireworks import Firework

WIN_W, WIN_H = 1000, 800


def make_firework():
	return Firework(0.0, 1.0, 0.0, angle_deg=110, color=(0.0, 0.9, 0.15))


def run():
	pygame.init()
	pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
	pygame.display.set_caption("Firework test")

	glClearColor(0.0, 0.0, 0.0, 1.0)
	glEnable(GL_BLEND)
	glMatrixMode(GL_PROJECTION)
	gluPerspective(45.0, WIN_W / WIN_H, 0.1, 100.0)
	glMatrixMode(GL_MODELVIEW)

	firework = make_firework()
	clock = pygame.time.Clock()
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				running = False

		firework.update()
		if firework.done:
			firework = make_firework()

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, -0.5, -9.0)
		firework.draw()

		pygame.display.flip()
		clock.tick(60)
	pygame.quit()


if __name__ == "__main__":
	run()
