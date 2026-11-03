"""Small immediate-mode OpenGL helpers shared by the C64 case and its keys.

All drawing here is meant to be recorded into display lists, so it favours
clarity over speed. Normals are derived from the vertex winding; the demo turns
on two-sided lighting, so a face lights correctly whichever way it is wound.
"""

import math

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps

_fonts = {}


def face_normal(p0, p1, p2):
	ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
	vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
	nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
	length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
	return nx / length, ny / length, nz / length


def quad(p0, p1, p2, p3):
	"""Emit one flat quad; call between glBegin(GL_QUADS) / glEnd()."""
	glNormal3f(*face_normal(p0, p1, p2))
	for corner in (p0, p1, p2, p3):
		glVertex3f(*corner)


def textured_quad(texture, p0, p1, p2, p3):
	"""Quad with the texture's bottom-left on p0, bottom-right p1, top-right p2, top-left p3."""
	glEnable(GL_TEXTURE_2D)
	glBindTexture(GL_TEXTURE_2D, texture)
	glBegin(GL_QUADS)
	glNormal3f(*face_normal(p0, p1, p2))
	for corner, (s, t) in zip((p0, p1, p2, p3), ((0, 0), (1, 0), (1, 1), (0, 1))):
		glTexCoord2f(s, t)
		glVertex3f(*corner)
	glEnd()
	glDisable(GL_TEXTURE_2D)


def color(rgb, shade=1.0):
	glColor3f(rgb[0] * shade / 255.0, rgb[1] * shade / 255.0, rgb[2] * shade / 255.0)


def _font(size_px):
	if size_px not in _fonts:
		_fonts[size_px] = pygame.font.SysFont("arial", size_px, bold=True)
	return _fonts[size_px]


def _render_fitted(text, size_px, ink, max_width):
	"""Render text, shrinking the font until it fits max_width pixels."""
	while True:
		image = _font(size_px).render(text, True, ink)
		if image.get_width() <= max_width or size_px <= 8:
			return image
		size_px -= 2


def upload_texture(surface):
	width, height = surface.get_size()
	data = pygame.image.tobytes(surface, "RGBA", True)
	texture = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, texture)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE, data)
	return texture


def image_texture(path):
	"""Load an image file; returns (texture, width / height)."""
	surface = pygame.image.load(path)
	return upload_texture(surface), surface.get_width() / surface.get_height()


def text_texture(width_px, height_px, background, lines, squares=()):
	"""Paint text (and optional outlined squares) onto a texture.

	background - RGB(A) fill; pass an RGBA with alpha 0 for a transparent label.
	lines      - (text, font_px, ink, (x, y)) or (text, font_px, ink, (x, y), anchor):
	             (x, y) are fractions of the texture size measured from the top-left,
	             anchor is the pygame Rect point placed there ("center" by default,
	             e.g. "topleft" to left-align).
	squares    - (side_px, line_px, ink, (centre_x, centre_y)), centre as fractions
	             like the text positions.
	"""
	surface = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
	surface.fill(background)
	margin = width_px * 0.08
	for text, font_px, ink, (x, y), *anchor in lines:
		image = _render_fitted(text, font_px, ink, width_px - 2 * margin)
		position = (int(x * width_px), int(y * height_px))
		surface.blit(image, image.get_rect(**{anchor[0] if anchor else "center": position}))
	for side_px, line_px, ink, (centre_x, centre_y) in squares:
		square = pygame.Rect(0, 0, side_px, side_px)
		square.center = (int(centre_x * width_px), int(centre_y * height_px))
		pygame.draw.rect(surface, ink, square, line_px)
	return upload_texture(surface)
