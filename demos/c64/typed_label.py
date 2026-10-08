"""Text typed letter by letter (lib.typer.Typer) and shown as a quad in 3D.

The Typer draws onto an off-screen pygame surface sized for the whole text, so
the label keeps its size while it fills up from the left; the surface goes to
a texture whenever a new letter appears.
"""

import pygame
from OpenGL.GL import *

from demos.c64.geometry import upload_texture
from lib.typer import FONT_PATH, Typer


class TypedLabel:

	def __init__(self, text, height, frames_per_letter=4, font_px=48, beeping=True, font_path=FONT_PATH):
		self.text = text
		self.font_path = font_path
		self.height = height
		self.frames_per_letter = frames_per_letter
		self.font_px = font_px
		self.beeping = beeping
		self.frame = 0
		self._shown_letters = -1
		self._texture = None

	def build(self):
		"""Create the surface and the Typer. Needs pygame initialised."""
		pygame.font.init()
		width_px, height_px = pygame.font.Font(self.font_path, self.font_px).size(self.text)
		self._surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
		self.aspect = width_px / height_px
		self._new_typer()

	def _new_typer(self):
		self.typer = Typer(0, self.text, self._surface, 0, 0, self.font_px, self.font_path)
		self.typer.speed = self.frames_per_letter

	@property
	def finished(self):
		return self.frame >= len(self.text) * self.frames_per_letter

	def restart(self):
		self.frame = 0
		self._shown_letters = -1
		self._new_typer()

	def update(self):
		self.frame += 1
		letters = min(len(self.text), self.frame // self.frames_per_letter)
		if letters == self._shown_letters:
			return
		self._surface.fill((0, 0, 0, 0))
		self.typer.type(self.frame, beeping=self.beeping)
		if self._texture:
			glDeleteTextures([self._texture])
		self._texture = upload_texture(self._surface)
		self._shown_letters = letters

	def draw(self, centre, right, up):
		"""Quad centred on `centre`, spanning the unit `right` and `up` directions."""
		if not self._texture:
			return
		half_width, half_height = self.height * self.aspect / 2, self.height / 2
		glDisable(GL_LIGHTING)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self._texture)
		glColor3f(1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		for (s, t), (across, along) in (((0, 0), (-1, -1)), ((1, 0), (1, -1)), ((1, 1), (1, 1)), ((0, 1), (-1, 1))):
			glTexCoord2f(s, t)
			glVertex3f(*(c + across * half_width * r + along * half_height * u for c, r, u in zip(centre, right, up)))
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_BLEND)
		glEnable(GL_LIGHTING)

	def destroy(self):
		if self._texture:
			glDeleteTextures([self._texture])
			self._texture = None
