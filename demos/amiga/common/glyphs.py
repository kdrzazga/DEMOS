"""Glyph masks -> bevel-normal textures, plus a painter for rounded-square "extended" letters.

A texture stores a bevel normal in RGB (from a blurred alpha mask) and coverage in A,
so a flat quad can be lit like an embossed letter (see common/glsl.py, GLYPH_*).
"""
import os
from dataclasses import dataclass

import numpy as np
import pygame
from PIL import Image, ImageFilter

from demos.amiga.common.gl_util import upload_rgba_texture

FONTS_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
WHITE = (255, 255, 255, 255)


@dataclass
class GlyphSprite:
	texture: int
	width: float        # world units, padding included
	height: float
	center_x: float     # world position of the quad centre (used by static layouts)
	center_y: float
	slant: float


def mask_to_bevel_rgba(mask, bevel_px):
	"""mask: float32 (h, w) in 0..1, row 0 = top. Returns GL-ready RGBA uint8 (row 0 = bottom)."""
	mask_image = Image.fromarray((mask * 255).astype(np.uint8))
	height_field = np.asarray(mask_image.filter(ImageFilter.GaussianBlur(bevel_px)), np.float32) / 255.0
	slope_rows, slope_cols = np.gradient(height_field)
	steepness = bevel_px * 2.2
	# rows run downward in the image, so "up" slope is -slope_rows
	normal = np.dstack((-slope_cols * steepness, slope_rows * steepness, np.ones_like(height_field)))
	normal /= np.linalg.norm(normal, axis=2, keepdims=True)
	rgba = np.empty(mask.shape + (4,), np.uint8)
	rgba[..., :3] = ((normal * 0.5 + 0.5) * 255).astype(np.uint8)
	rgba[..., 3] = (mask * 255).astype(np.uint8)
	return np.flipud(rgba)


def surface_alpha(surface):
	return pygame.surfarray.array_alpha(surface).T.astype(np.float32) / 255.0


def embolden(mask, radius):
	if radius <= 0:
		return mask
	image = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * radius + 1))
	return np.asarray(image, np.float32) / 255.0


def crop_to_ink_rows(mask, threshold=0.1):
	ink_rows = np.where(mask.max(axis=1) > threshold)[0]
	return mask[ink_rows[0]:ink_rows[-1] + 1]


def join_horizontally(masks, gap_px):
	height = max(mask.shape[0] for mask in masks)
	parts = []
	for index, mask in enumerate(masks):
		if index:
			parts.append(np.zeros((height, gap_px), np.float32))
		parts.append(np.pad(mask, ((height - mask.shape[0], 0), (0, 0))))
	return np.hstack(parts)


class SpriteFactory:
	"""Turns masks into GlyphSprites in world units."""

	def __init__(self, bevel_px=5, pad_px=12):
		self.bevel_px = bevel_px
		self.pad_px = pad_px

	def make(self, mask, world_per_px, left=0.0, bottom=0.0, slant=0.0, horizontal_fit=1.0):
		padded = np.pad(mask, self.pad_px)
		texture = upload_rgba_texture(mask_to_bevel_rgba(padded, self.bevel_px))
		height_px, width_px = padded.shape
		width, height = width_px * world_per_px * horizontal_fit, height_px * world_per_px
		pad = self.pad_px * world_per_px
		return GlyphSprite(texture, width, height, left - pad * horizontal_fit + width / 2, bottom - pad + height / 2, slant)

	def make_by_height(self, mask, height, left=0.0, bottom=0.0, slant=0.0):
		return self.make(mask, height / mask.shape[0], left, bottom, slant)


class RoundedGlyphPainter:
	"""Draws rounded-square glyphs (Eurostile / Microgramma flavour) at 2x and downsamples for antialiasing.
	width_ratio > 1 gives the extended CD32 look, < 1 the condensed CDTV look."""

	def __init__(self, glyph_height, width_ratio, stroke_ratio, outer_radius_ratio, supersample=2):
		self.supersample = supersample
		self.height = glyph_height * supersample
		self.width = int(self.height * width_ratio)
		self.stroke = int(self.height * stroke_ratio)
		self.radius = int(self.height * outer_radius_ratio)

	def _canvas(self):
		return pygame.Surface((self.width, self.height), pygame.SRCALPHA)

	def _outline(self, surface, rect, top_left=0, top_right=0, bottom_left=0, bottom_right=0):
		pygame.draw.rect(surface, WHITE, rect, self.stroke,
			border_top_left_radius=top_left, border_top_right_radius=top_right,
			border_bottom_left_radius=bottom_left, border_bottom_right_radius=bottom_right)

	@staticmethod
	def _erase(surface, rect):
		surface.fill((0, 0, 0, 0), rect)

	def _finish(self, surface):
		size = (self.width // self.supersample, self.height // self.supersample)
		return surface_alpha(pygame.transform.smoothscale(surface, size))

	def letter_c(self, opening=0.28):
		surface = self._canvas()
		width, height, stroke, radius = self.width, self.height, self.stroke, self.radius
		self._outline(surface, (0, 0, width, height), radius, radius, radius, radius)
		gap_top = int(height * (0.5 - opening / 2))
		self._erase(surface, (width - stroke - 2, gap_top, stroke + 2, int(height * opening)))
		return self._finish(surface)

	def letter_d(self):
		surface = self._canvas()
		small = self.stroke // 3
		self._outline(surface, (0, 0, self.width, self.height), small, self.radius, small, self.radius)
		return self._finish(surface)

	def letter_t(self, stem_ratio=1.15):
		surface = self._canvas()
		width, height, stroke = self.width, self.height, self.stroke
		stem = int(stroke * stem_ratio)
		surface.fill(WHITE, (0, 0, width, stroke))
		surface.fill(WHITE, ((width - stem) // 2, 0, stem, height))
		return self._finish(surface)

	def letter_v(self):
		surface = self._canvas()
		width, height, stroke = self.width, self.height, self.stroke
		arm = stroke * 1.15
		half_foot = stroke * 0.62
		points = ((0, 0), (arm, 0), (width / 2, height - stroke * 1.25), (width - arm, 0), (width, 0),
			(width / 2 + half_foot, height), (width / 2 - half_foot, height))
		pygame.draw.polygon(surface, WHITE, points)
		return self._finish(surface)

	def digit_3(self):
		surface = self._canvas()
		width, height, stroke, radius = self.width, self.height, self.stroke, self.radius
		self._outline(surface, (0, 0, width, height), 0, radius, 0, radius)
		self._erase(surface, (0, stroke, stroke + 1, height - 2 * stroke))
		middle_left = int(width * 0.28)
		surface.fill(WHITE, (middle_left, (height - stroke) // 2, width - middle_left - stroke // 2, stroke))
		return self._finish(surface)

	def digit_2(self):
		surface = self._canvas()
		width, height, stroke, radius = self.width, self.height, self.stroke, self.radius
		half = (height + stroke) // 2
		middle_radius = radius // 2
		self._outline(surface, (0, 0, width, half), 0, radius, middle_radius, middle_radius)
		self._erase(surface, (0, stroke, stroke + 1, half - stroke))
		lower_top = height - half
		self._outline(surface, (0, lower_top, width, half), middle_radius, middle_radius, 0, 0)
		self._erase(surface, (width - stroke - 1, lower_top + stroke, stroke + 1, half - 2 * stroke))
		return self._finish(surface)

	def glyph(self, character):
		return {"C": self.letter_c, "D": self.letter_d, "T": self.letter_t, "V": self.letter_v,
			"2": self.digit_2, "3": self.digit_3}[character]()
