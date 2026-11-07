import numpy as np
import pygame
from OpenGL.GL import *


class OutlineStrengthMap:

	def __init__(self):
		self.brightness_limit = 160.0

	def build(self, surface):
		alpha = pygame.surfarray.array_alpha(surface).T
		brightest_channel = pygame.surfarray.array3d(surface).transpose(1, 0, 2).max(axis=2).astype(np.float32)
		strength = np.clip(1.0 - brightest_channel / self.brightness_limit, 0.0, 1.0) * (alpha > 0)
		return (strength * 255.0).astype(np.uint8)


class SprayOrderMap:

	def __init__(self, seed):
		self.random = np.random.default_rng(seed)
		self.sweep_weight = 0.68
		self.blotch_weight = 0.24
		self.speckle_weight = 0.08
		self.blotch_cells = 7
		self.fill_share = 0.72
		self.outline_start = 0.66
		self.outline_brightness_limit = 70
		self.row_sweep_weight = 0.8
		self.column_sweep_weight = 0.2

	def build(self, surface):
		width, height = surface.get_size()
		alpha = pygame.surfarray.array_alpha(surface).T
		colors = pygame.surfarray.array3d(surface).transpose(1, 0, 2)
		rows, columns = np.mgrid[0:height, 0:width].astype(np.float32)
		row_fraction = rows / max(1, height - 1)
		column_fraction = columns / max(1, width - 1)
		sweep = (row_fraction * self.row_sweep_weight + column_fraction * self.column_sweep_weight
		         + 0.05 * np.sin(column_fraction * 17.0 + row_fraction * 5.0))
		order = (sweep * self.sweep_weight
		         + self._blotches(width, height) * self.blotch_weight
		         + self.random.random((height, width), dtype=np.float32) * self.speckle_weight)
		painted = alpha > 0
		if painted.any():
			lowest, highest = order[painted].min(), order[painted].max()
			order = (order - lowest) / max(1e-6, highest - lowest)
		outline = painted & (colors.max(axis=2) < self.outline_brightness_limit)
		order = np.where(outline, self.outline_start + (1.0 - self.outline_start) * order, order * self.fill_share)
		return (np.clip(order, 0.0, 1.0) * 255.0).astype(np.uint8)

	def _blotches(self, width, height):
		coarse = (self.random.random((self.blotch_cells, self.blotch_cells)) * 255).astype(np.uint8)
		coarse_surface = pygame.surfarray.make_surface(np.repeat(coarse[:, :, None], 3, axis=2))
		smooth_surface = pygame.transform.smoothscale(coarse_surface, (width, height))
		return pygame.surfarray.array3d(smooth_surface)[:, :, 0].T.astype(np.float32) / 255.0


class SprayTexture:

	def __init__(self, glyph, seed, order_map=None):
		self.glyph = glyph
		self.width, self.height = glyph.size
		self.art_texture = self._upload_art(glyph.surface)
		self.order_texture = self._upload_order_and_outline((order_map or SprayOrderMap(seed)).build(glyph.surface),
		                                                    OutlineStrengthMap().build(glyph.surface))

	@staticmethod
	def _new_texture():
		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		return texture

	def _upload_art(self, surface):
		texture = self._new_texture()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             pygame.image.tobytes(surface, "RGBA"))
		return texture

	def _upload_order_and_outline(self, order, outline_strength):
		texture = self._new_texture()
		order_and_outline = np.ascontiguousarray(np.stack([order, outline_strength], axis=2))
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE_ALPHA, self.width, self.height, 0, GL_LUMINANCE_ALPHA,
		             GL_UNSIGNED_BYTE, order_and_outline.tobytes())
		glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
		return texture

	def bind(self):
		glActiveTexture(GL_TEXTURE1)
		glBindTexture(GL_TEXTURE_2D, self.order_texture)
		glActiveTexture(GL_TEXTURE0)
		glBindTexture(GL_TEXTURE_2D, self.art_texture)
