import os

import numpy as np
import pygame

GRAFFITI_RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources", "graffiti")
SHEET_PATH = os.path.join(GRAFFITI_RESOURCES, "graffittiKA.png")


class GraffitiGlyph:

	def __init__(self, name, surface, cell_offset):
		self.name = name
		self.surface = surface
		self.cell_offset = cell_offset

	@classmethod
	def from_resource(cls, name, file_name):
		return cls(name, pygame.image.load(os.path.join(GRAFFITI_RESOURCES, file_name)).copy(), (0, 0))

	@property
	def size(self):
		return self.surface.get_size()

	@property
	def average_fill_color(self):
		colors = pygame.surfarray.array3d(self.surface).reshape(-1, 3).astype(np.float32)
		alphas = pygame.surfarray.array_alpha(self.surface).reshape(-1)
		filled = (alphas > 200) & (colors.max(axis=1) > 90)
		return tuple(int(channel) for channel in colors[filled].mean(axis=0))


class GraffitiSheet:

	def __init__(self, path=SHEET_PATH):
		self.cell_width = 403
		self.cell_height = 611
		self.minimum_blob_pixels = 60
		self.trim_padding = 3
		self.letter_cells = {
			"K": (0, 0), "M1": (1, 0), "D": (2, 0), "A1": (3, 0),
			"A2": (0, 1), "M2": (1, 1), "I": (2, 1), "G": (3, 1), "A3": (4, 1),
		}
		self.special_cell_column = 4
		self.special_cell_split_row = 305
		self.sheet = self._load_without_grid(path)
		self.glyphs = self._cut_glyphs()

	def __getitem__(self, name):
		return self.glyphs[name]

	def _load_without_grid(self, path):
		sheet = pygame.image.load(path).copy()
		sheet_width, sheet_height = sheet.get_size()
		alpha = pygame.surfarray.pixels_alpha(sheet)
		for grid_x in range(self.cell_width, sheet_width, self.cell_width):
			alpha[grid_x, :] = 0
		for grid_y in range(self.cell_height, sheet_height, self.cell_height):
			alpha[:, grid_y] = 0
		special_left = self.special_cell_column * self.cell_width
		alpha[special_left:, self.special_cell_split_row] = 0
		del alpha
		return sheet

	def _cut_glyphs(self):
		glyphs = {}
		for name, (column, row) in self.letter_cells.items():
			cell_rect = pygame.Rect(column * self.cell_width, row * self.cell_height, self.cell_width, self.cell_height)
			glyphs[name] = self._trimmed_glyph(name, cell_rect)
		special_left = self.special_cell_column * self.cell_width
		special_width = self.sheet.get_width() - special_left
		plus_rect = pygame.Rect(special_left, 0, special_width, self.special_cell_split_row)
		ampersand_rect = pygame.Rect(special_left, self.special_cell_split_row,
		                             special_width, self.cell_height - self.special_cell_split_row)
		glyphs["PLUS"] = self._trimmed_glyph("PLUS", plus_rect)
		glyphs["AMPERSAND"] = self._trimmed_glyph("AMPERSAND", ampersand_rect)
		return glyphs

	def _trimmed_glyph(self, name, cell_rect):
		cell = self.sheet.subsurface(cell_rect).copy()
		cell_mask = pygame.mask.from_surface(cell, 1)
		blobs = [blob for blob in cell_mask.connected_components(self.minimum_blob_pixels)
		         if self._is_not_grid_remnant(blob)]
		kept_mask = pygame.mask.Mask(cell.get_size())
		for blob in blobs:
			kept_mask.draw(blob, (0, 0))
		kept_alpha = pygame.surfarray.array_alpha(
			kept_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)))
		cell_alpha = pygame.surfarray.pixels_alpha(cell)
		cell_alpha[kept_alpha == 0] = 0
		del cell_alpha
		bounds = kept_mask.get_bounding_rects()
		content_rect = bounds[0].unionall(bounds[1:]).inflate(self.trim_padding * 2, self.trim_padding * 2)
		content_rect = content_rect.clip(cell.get_rect())
		return GraffitiGlyph(name, cell.subsurface(content_rect).copy(), content_rect.topleft)

	@staticmethod
	def _is_not_grid_remnant(blob):
		blob_rect = blob.get_bounding_rects()[0]
		return min(blob_rect.width, blob_rect.height) > 2
