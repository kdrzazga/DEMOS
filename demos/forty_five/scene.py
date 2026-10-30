"""OpenGL state shared by everything that shows the Commodore 64 model."""

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective


def setup_scene(aspect, fov, background=(0.0, 0.0, 0.0), near=1.0, far=400.0):
	"""Depth test, one directional light with two-sided lighting, colour-tracked
	materials and the perspective projection. The light's position is set later,
	per frame, by whoever owns the camera."""
	glClearColor(*background, 1.0)
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_NORMALIZE)
	glShadeModel(GL_SMOOTH)

	glEnable(GL_LIGHTING)
	glEnable(GL_LIGHT0)
	glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
	glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
	glLightfv(GL_LIGHT0, GL_AMBIENT, (0.38, 0.38, 0.38, 1.0))
	glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.75, 0.75, 0.72, 1.0))
	glLightfv(GL_LIGHT0, GL_SPECULAR, (0.15, 0.15, 0.15, 1.0))
	glEnable(GL_COLOR_MATERIAL)
	glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
	glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.3, 0.3, 0.3, 1.0))
	glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 24.0)

	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(fov, aspect, near, far)
	glMatrixMode(GL_MODELVIEW)
