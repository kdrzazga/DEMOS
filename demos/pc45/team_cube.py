import os

import pygame
from OpenGL.GL import *


class TeamCube:

	def __init__(self, res_path, images, half_size=1.0, spin=0.8):
		self.half = half_size
		self.spin = spin
		self.side_color = (0.12, 0.12, 0.14)
		self.angle = 0.0
		self.texs = []
		for image in images:
			surface = pygame.image.load(os.path.join(res_path, image))
			tex = glGenTextures(1)
			glBindTexture(GL_TEXTURE_2D, tex)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0,
			             GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(surface, "RGBA", True))
			self.texs.append(tex)

	def update(self):
		self.angle += self.spin

	def draw(self):
		s = self.half
		glPushMatrix()
		glRotatef(self.angle, 0.0, 1.0, 0.0)
		glColor3f(1.0, 1.0, 1.0)
		glEnable(GL_TEXTURE_2D)
		faces = (
			(self.texs[0], (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)),
			(self.texs[1], (s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)),
			(self.texs[2], (s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)),
			(self.texs[3], (-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)),
		)
		for tex, a, b, c, d in faces:
			glBindTexture(GL_TEXTURE_2D, tex)
			glBegin(GL_QUADS)
			glTexCoord2f(0.0, 0.0); glVertex3f(*a)
			glTexCoord2f(1.0, 0.0); glVertex3f(*b)
			glTexCoord2f(1.0, 1.0); glVertex3f(*c)
			glTexCoord2f(0.0, 1.0); glVertex3f(*d)
			glEnd()
		glDisable(GL_TEXTURE_2D)
		glColor3f(*self.side_color)
		glBegin(GL_QUADS)
		glVertex3f(-s, s, s); glVertex3f(s, s, s); glVertex3f(s, s, -s); glVertex3f(-s, s, -s)
		glVertex3f(-s, -s, -s); glVertex3f(s, -s, -s); glVertex3f(s, -s, s); glVertex3f(-s, -s, s)
		glEnd()
		glEnable(GL_TEXTURE_2D)
		glPopMatrix()

	def destroy(self):
		for tex in self.texs:
			glDeleteTextures([tex])
