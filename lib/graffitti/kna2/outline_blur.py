import numpy as np
import pygame

from lib.graffitti.kna2.bayer_dither import BayerDither


class OutlineBlur:

	def __init__(self):
		self.color = (0, 0, 0)
		self.width = 40.0
		self.strength = 0.9
		self.falloff_power = 1.6
		self.dither = BayerDither()

	def apply(self, fill_surface, blurred_area):
		colors = pygame.surfarray.pixels3d(fill_surface)
		colors[blurred_area] = self.color
		del colors

	def blurred_area(self, outline, interior_area, line_width):
		reach = self.width + line_width / 2 + 2.0
		distance_from_line_edge = self._distance_from_outline(outline, interior_area.shape, reach) - line_width / 2
		closeness = np.clip(1.0 - distance_from_line_edge / self.width, 0.0, 1.0)
		intensity = self.strength * closeness ** self.falloff_power
		return interior_area & self.dither.dotted_area(intensity)

	def _distance_from_outline(self, outline, size, reach):
		distance = np.full(size, np.inf, dtype=np.float32)
		for segment in outline.segments:
			self._measure_segment(distance, segment, reach)
		return distance

	@staticmethod
	def _measure_segment(distance, segment, reach):
		width, height = distance.shape
		start_x, start_y = segment.start
		end_x, end_y = segment.end
		left = max(0, int(min(start_x, end_x) - reach))
		right = min(width, int(max(start_x, end_x) + reach) + 2)
		top = max(0, int(min(start_y, end_y) - reach))
		bottom = min(height, int(max(start_y, end_y) + reach) + 2)
		if left >= right or top >= bottom:
			return
		columns, rows = np.mgrid[left:right, top:bottom].astype(np.float32) + 0.5
		run_x, run_y = end_x - start_x, end_y - start_y
		along = np.clip(((columns - start_x) * run_x + (rows - start_y) * run_y)
		                / max(1e-6, run_x * run_x + run_y * run_y), 0.0, 1.0)
		segment_distance = np.hypot(columns - (start_x + along * run_x), rows - (start_y + along * run_y))
		region = distance[left:right, top:bottom]
		np.minimum(region, segment_distance, out=region)
