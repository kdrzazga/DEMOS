import pygame


class LetterInterior:

	def __init__(self, line_surface, line_width):
		self.alpha_threshold = 60
		self.spread_under_line = max(1, line_width // 3)
		self.size = line_surface.get_size()
		line_mask = pygame.mask.from_surface(line_surface, self.alpha_threshold)
		free_mask = line_mask.copy()
		free_mask.invert()
		outside = free_mask.connected_component((0, 0))
		outer_lines = self._union(line for line in line_mask.connected_components()
		                          if self._touch(line, outside))
		enclosed_regions = [region for region in free_mask.connected_components() if not region.get_at((0, 0))]
		body = self._union(region for region in enclosed_regions if self._touch(region, outer_lines))
		self.area = self._as_array(self._grown(body, self.spread_under_line))

	def _union(self, masks):
		union = pygame.mask.Mask(self.size)
		for mask in masks:
			union.draw(mask, (0, 0))
		return union

	def _grown(self, mask, pixels):
		brush = pygame.mask.Mask((2 * pixels + 1, 2 * pixels + 1), fill=True)
		grown = pygame.mask.Mask(self.size)
		grown.draw(mask.convolve(brush), (-pixels, -pixels))
		return grown

	def _touch(self, mask, other_mask):
		return mask.overlap_area(self._grown(other_mask, 1), (0, 0)) > 0

	@staticmethod
	def _as_array(mask):
		surface = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
		return pygame.surfarray.array_alpha(surface) > 0
