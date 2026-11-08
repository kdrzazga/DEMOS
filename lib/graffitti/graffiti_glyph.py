import os

import numpy as np
import pygame

GRAFFITI_RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources", "graffiti")


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
