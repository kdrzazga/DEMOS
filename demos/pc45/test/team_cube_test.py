"""Standalone demo of the TeamCube (pygame + OpenGL).

    python -m demos.pc45.test.team_cube_test

Shows the four team photos on the side walls of a slowly spinning cube, placed
in the bottom-right corner of the window at ~15% of the window size.
ESC / window-close quits.
"""

import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__))))))

from demos.pc45.team_cube import TeamCube

WIN_W, WIN_H = 1000, 800
RES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
IMAGES = (
	"team/DonEstridge.png",
	"team/mark-dean.png",
	"team/DennisL.Moeller.png",
	"team/wiliamLowe.png",
)
CUBE_FRACTION = 0.15
MARGIN = 20


def run():
	pygame.init()
	pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
	pygame.display.set_caption("Team cube test")

	cube = TeamCube(RES_PATH, IMAGES)
	clock = pygame.time.Clock()
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				running = False

		glViewport(0, 0, WIN_W, WIN_H)
		glClearColor(0.08, 0.09, 0.11, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		rw = int(WIN_W * CUBE_FRACTION)
		rh = int(WIN_H * CUBE_FRACTION)
		glViewport(MARGIN, MARGIN, rw, rh)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(45.0, rw / rh, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glEnable(GL_DEPTH_TEST)
		glTranslatef(0.0, 0.0, -4.5)
		glRotatef(18.0, 1.0, 0.0, 0.0)
		cube.update()
		cube.draw()

		pygame.display.flip()
		clock.tick(60)

	cube.destroy()
	pygame.quit()


if __name__ == "__main__":
	run()
