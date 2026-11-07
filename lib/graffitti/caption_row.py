class CaptionRow:

	def __init__(self, glyphs, scale=1.0, kerning=28, offsets=None):
		self.glyphs = glyphs
		self.scale = scale
		self.kerning = kerning
		self.offsets = offsets or {}

	def _rects_from_origin(self):
		cursor_x = 0.0
		rects = []
		for index, glyph in enumerate(self.glyphs):
			offset_x, offset_y = self.offsets.get(index, (0, 0))
			glyph_width, glyph_height = glyph.size[0] * self.scale, glyph.size[1] * self.scale
			glyph_top = (glyph.cell_offset[1] + offset_y) * self.scale
			rects.append((cursor_x + offset_x * self.scale, glyph_top, glyph_width, glyph_height))
			cursor_x += glyph_width - self.kerning * self.scale
		return rects

	@property
	def width(self):
		rects = self._rects_from_origin()
		return max(left + width for left, _, width, _ in rects) - min(left for left, _, _, _ in rects)

	@property
	def height(self):
		rects = self._rects_from_origin()
		return max(top + height for _, top, _, height in rects) - min(top for _, top, _, _ in rects)

	def centers(self, center_x, top_y):
		rects = self._rects_from_origin()
		shift_x = center_x - self.width / 2 - min(left for left, _, _, _ in rects)
		shift_y = top_y - min(top for _, top, _, _ in rects)
		return [(left + width / 2 + shift_x, top + height / 2 + shift_y) for left, top, width, height in rects]
