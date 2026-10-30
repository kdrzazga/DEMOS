import pygame
from OpenGL.GL import *

from demos.forty_five.geometry import upload_texture


class BoardPhoto:

	def __init__(self, path, cm_per_pixel):
		surface = pygame.image.load(path)
		self.width_px, self.height_px = surface.get_size()
		self.cm_per_pixel = cm_per_pixel
		self.texture = upload_texture(surface)

	def length(self, pixels):
		return pixels * self.cm_per_pixel

	def to_world(self, x_px, y_px):
		return ((x_px - self.width_px / 2) * self.cm_per_pixel,
		        (y_px - self.height_px / 2) * self.cm_per_pixel)

	def world_rect(self, rect):
		left, back = self.to_world(rect.left, rect.top)
		right, front = self.to_world(rect.right, rect.bottom)
		return left, back, right, front

	def to_texture(self, world_x, world_z):
		x_px = world_x / self.cm_per_pixel + self.width_px / 2
		y_px = world_z / self.cm_per_pixel + self.height_px / 2
		return x_px / self.width_px, 1.0 - y_px / self.height_px

	def begin(self):
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glColor3f(1.0, 1.0, 1.0)

	def end(self):
		glDisable(GL_TEXTURE_2D)

	def vertex(self, x, y, z):
		glTexCoord2f(*self.to_texture(x, z))
		glVertex3f(x, y, z)
