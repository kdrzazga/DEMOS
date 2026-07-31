"""A photo extruded into a thin 3D slab for pygame + OpenGL.

The front face carries the picture; the four sides and the back are a flat
colour, giving the image a small physical depth (depth_px, measured in the
image's own pixels). The caller owns the camera and should have depth testing
enabled; draw() only emits geometry in world space.
"""

import pygame
from OpenGL.GL import *


class ExtrudedPhoto:

	SIDE_COLOR = (0.22, 0.22, 0.25)

	def __init__(self, path, half_height, depth_px):
		surface = pygame.image.load(path)
		self.img_w, self.img_h = surface.get_size()
		data = pygame.image.tostring(surface, "RGBA", True)
		self.tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.tex)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.img_w, self.img_h, 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, data)
		self.hh = half_height
		self.hw = half_height * (self.img_w / self.img_h)
		self.hd = depth_px * (half_height / self.img_h)

	def draw(self):
		hw, hh, hd = self.hw, self.hh, self.hd
		glColor3f(1.0, 1.0, 1.0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.tex)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex3f(-hw, -hh, hd)
		glTexCoord2f(1.0, 0.0); glVertex3f(hw, -hh, hd)
		glTexCoord2f(1.0, 1.0); glVertex3f(hw, hh, hd)
		glTexCoord2f(0.0, 1.0); glVertex3f(-hw, hh, hd)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glColor3f(*self.SIDE_COLOR)
		glBegin(GL_QUADS)
		glVertex3f(hw, -hh, hd); glVertex3f(hw, -hh, -hd); glVertex3f(hw, hh, -hd); glVertex3f(hw, hh, hd)
		glVertex3f(-hw, -hh, -hd); glVertex3f(-hw, -hh, hd); glVertex3f(-hw, hh, hd); glVertex3f(-hw, hh, -hd)
		glVertex3f(-hw, hh, hd); glVertex3f(hw, hh, hd); glVertex3f(hw, hh, -hd); glVertex3f(-hw, hh, -hd)
		glVertex3f(-hw, -hh, -hd); glVertex3f(hw, -hh, -hd); glVertex3f(hw, -hh, hd); glVertex3f(-hw, -hh, hd)
		glVertex3f(hw, -hh, -hd); glVertex3f(-hw, -hh, -hd); glVertex3f(-hw, hh, -hd); glVertex3f(hw, hh, -hd)
		glEnd()
		glEnable(GL_TEXTURE_2D)

	def destroy(self):
		glDeleteTextures([self.tex])
