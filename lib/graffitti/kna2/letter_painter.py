import math

import pygame

from lib.graffitti.graffiti_glyph import GraffitiGlyph
from lib.graffitti.kna2.color_gradient import GradientPalette
from lib.graffitti.kna2.letter_interior import LetterInterior
from lib.graffitti.kna2.outline_blur import OutlineBlur
from lib.graffitti.kna2.stroke_order_map import StrokeOrderMap


class PaintedLetter:

	def __init__(self, line_glyph, order_map, total_length, fill_glyphs):
		self.line_glyph = line_glyph
		self.order_map = order_map
		self.total_length = total_length
		self.fill_glyphs = fill_glyphs

	@property
	def center(self):
		return (self.line_glyph.cell_offset[0] + self.line_glyph.size[0] / 2,
		        self.line_glyph.cell_offset[1] + self.line_glyph.size[1] / 2)


class LetterPainter:

	def __init__(self):
		self.scale = 3.0
		self.line_width = 12
		self.line_color = (0, 0, 0)
		self.supersampling = 2
		self.palette = GradientPalette()
		self.outline_blur = OutlineBlur()

	@property
	def padding(self):
		return self.line_width

	def paint(self, outline, filled):
		scaled_outline = outline.transformed(self.scale, 0.0, 0.0)
		left, top, right, bottom = scaled_outline.bounds
		offset = (math.floor(left) - self.padding, math.floor(top) - self.padding)
		local_outline = scaled_outline.transformed(1.0, -offset[0], -offset[1])
		size = (math.ceil(right) - offset[0] + self.padding, math.ceil(bottom) - offset[1] + self.padding)
		line_surface = self._draw_lines(local_outline, size)
		fill_glyphs = self._paint_fills(local_outline, line_surface, offset) if filled else []
		return PaintedLetter(GraffitiGlyph(outline.name, line_surface, offset),
		                     StrokeOrderMap(local_outline, self.line_width), local_outline.total_length, fill_glyphs)

	def _paint_fills(self, local_outline, line_surface, offset):
		interior = LetterInterior(line_surface, self.line_width)
		blurred_area = self.outline_blur.blurred_area(local_outline, interior.area, self.line_width)
		return [GraffitiGlyph(f"{local_outline.name}_{gradient.name}",
		                      self._paint_fill(gradient, interior.area, blurred_area), offset)
		        for gradient in self.palette.gradients]

	def _paint_fill(self, gradient, interior_area, blurred_area):
		fill_surface = gradient.paint(interior_area)
		self.outline_blur.apply(fill_surface, blurred_area)
		return fill_surface

	def _draw_lines(self, outline, size):
		enlarged = pygame.Surface((size[0] * self.supersampling, size[1] * self.supersampling), pygame.SRCALPHA)
		enlarged.fill((*self.line_color, 0))
		for segment in outline.segments:
			self._draw_segment(enlarged, segment)
		return pygame.transform.smoothscale(enlarged, size)

	def _draw_segment(self, surface, segment):
		start = pygame.Vector2(segment.start) * self.supersampling
		end = pygame.Vector2(segment.end) * self.supersampling
		half_width = self.line_width * self.supersampling / 2
		direction = end - start
		if direction.length() > 0:
			sideways = direction.normalize().rotate(90) * half_width
			pygame.draw.polygon(surface, self.line_color,
			                    [start + sideways, end + sideways, end - sideways, start - sideways])
		pygame.draw.circle(surface, self.line_color, start, half_width)
		pygame.draw.circle(surface, self.line_color, end, half_width)
