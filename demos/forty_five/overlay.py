from contextlib import contextmanager

from OpenGL.GL import *


@contextmanager
def screen_overlay(extra_attribute_bits=0):
	glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | extra_attribute_bits)
	glDisable(GL_LIGHTING)
	glDisable(GL_DEPTH_TEST)
	glMatrixMode(GL_MODELVIEW)
	glPushMatrix()
	glLoadIdentity()
	try:
		yield
	finally:
		glPopMatrix()
		glPopAttrib()
