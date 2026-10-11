"""AMIGA CD32 logo glyphs.

"AMIGA"    - a bold serif italic (the original is ITC Garamond Bold Condensed Italic; Windows ships
             Garamond Bold upright, so the italic is a shear applied in the vertex shader).
"CD", "32" - procedural rounded-square strokes in the spirit of Eurostile / Microgramma Bold Extended.

Layout numbers come from the 480x360 reference video (1 world unit = 100 reference pixels).
"""
import os
from dataclasses import dataclass

import numpy as np
import pygame

from demos.amiga.common.glyphs import (FONTS_DIR, RoundedGlyphPainter, SpriteFactory, crop_to_ink_rows, embolden,
	join_horizontally, surface_alpha)


@dataclass
class SerifFontChoice:
	file_name: str
	slant: float       # horizontal shear per unit of height; fakes italic on an upright face
	embolden_px: int   # dilation at render size; Garamond Bold is lighter than the logo


DEFAULT_SERIF_FONTS = (
	SerifFontChoice("GARABD.TTF", slant=0.23, embolden_px=3),
	SerifFontChoice("timesbi.ttf", slant=0.0, embolden_px=0),
	SerifFontChoice("georgiaz.ttf", slant=0.0, embolden_px=0),
)


class Cd32LogoGlyphBuilder:

	def __init__(self, serif_fonts=DEFAULT_SERIF_FONTS, render_px=220, sprite_factory=None):
		self.serif_fonts = serif_fonts
		self.render_px = render_px
		self.sprites = sprite_factory or SpriteFactory()

	def _open_serif_font(self):
		for choice in self.serif_fonts:
			path = os.path.join(FONTS_DIR, choice.file_name)
			if os.path.exists(path):
				return pygame.font.Font(path, self.render_px), choice
		return pygame.font.Font(None, self.render_px), SerifFontChoice("default", slant=0.22, embolden_px=4)

	def build_amiga_letters(self, left=-2.10, baseline=0.68, cap_height=0.43, word_width=2.10):
		font, choice = self._open_serif_font()
		word = "AMIGA"
		letter_masks = [embolden(surface_alpha(font.render(letter, True, (255, 255, 255))), choice.embolden_px)
			for letter in word]
		# crop every letter to the common ink rows so they share a baseline
		ink_rows = np.where(np.max(np.vstack([mask.max(axis=1)[None, :] for mask in letter_masks]), axis=0) > 0.1)[0]
		top_row, bottom_row = ink_rows[0], ink_rows[-1] + 1
		letter_masks = [mask[top_row:bottom_row] for mask in letter_masks]
		world_per_px = cap_height / (bottom_row - top_row)
		advances = [font.size(word[:index])[0] for index in range(len(word) + 1)]
		horizontal_fit = word_width / (advances[-1] * world_per_px)
		sprites = []
		for index, mask in enumerate(letter_masks):
			letter_left = left + advances[index] * world_per_px * horizontal_fit
			sprites.append(self.sprites.make(mask, world_per_px, letter_left, baseline, choice.slant, horizontal_fit))
		return sprites

	def build_cd(self, left=0.15, bottom=0.68, height=0.37):
		painter = RoundedGlyphPainter(self.render_px, width_ratio=1.42, stroke_ratio=0.24, outer_radius_ratio=0.34)
		mask = join_horizontally([painter.letter_c(), painter.letter_d()], gap_px=int(self.render_px * 0.14))
		return self.sprites.make_by_height(mask, height, left, bottom)

	def build_32(self, left=1.38, bottom=0.92, height=0.27):
		painter = RoundedGlyphPainter(self.render_px, width_ratio=1.18, stroke_ratio=0.22, outer_radius_ratio=0.32)
		mask = join_horizontally([painter.digit_3(), painter.digit_2()], gap_px=int(self.render_px * 0.14))
		return self.sprites.make_by_height(mask, height, left, bottom)

	def build_trademark(self, left=2.08, bottom=1.12, height=0.085):
		path = os.path.join(FONTS_DIR, "arialbd.ttf")
		font = pygame.font.Font(path if os.path.exists(path) else None, self.render_px // 2)
		mask = crop_to_ink_rows(surface_alpha(font.render("TM", True, (255, 255, 255))))
		return self.sprites.make_by_height(mask, height, left, bottom)
