import numpy as np
import pygame

from lib.graffitti.graffiti_glyph import GraffitiGlyph
from lib.graffitti.kna2.bayer_dither import BayerDither


class DitheredFrame:

	def __init__(self, canvas_size, outlines, line_width, clear_border, dither_width, color):
		self.canvas_size = canvas_size
		self.outlines = outlines
		self.line_width = line_width
		self.clear_border = clear_border
		self.dither_width = dither_width
		self.color = color
		self.strength = 1.0
		self.falloff_power = 2.0
		self.dither = BayerDither()
		self.dither.irregularity = 0.55
		self.grid_size = self.dither.grid_size(canvas_size)
		self.distance_from_letters = self._distance_from_letters(self.grid_size)
		self.cell_thresholds = self.dither.cell_thresholds(self.grid_size)

	@property
	def dither_start_distance(self):
		return self.line_width / 2 + self.clear_border

	def paint(self):
		dotted_cells = (self._outside_letters(self.distance_from_letters)
		                & (self._intensity(self.distance_from_letters) > self.cell_thresholds))
		surface = pygame.Surface(self.canvas_size, pygame.SRCALPHA)
		surface.fill((*self.color, 0))
		alpha = pygame.surfarray.pixels_alpha(surface)
		alpha[self.dither.enlarged(dotted_cells, self.canvas_size)] = 255
		del alpha
		return GraffitiGlyph("FRAME", surface, (0, 0))

	def paint_blackout(self):
		surface = pygame.Surface(self.canvas_size, pygame.SRCALPHA)
		surface.fill((*self.color, 255))
		return GraffitiGlyph("BLACKOUT", surface, (0, 0))

	def blackout_order_map(self):
		return DitherSpreadOrderMap(self)

	def spread_needed_by_cells(self):
		dither_reach = self.dither_width * (self.cell_thresholds / self.strength) ** (1.0 / self.falloff_power)
		full_spread = self.dither_start_distance + self.dither_width
		return np.clip((self.dither_start_distance + dither_reach - self.distance_from_letters) / full_spread, 0.0, 1.0)

	def _intensity(self, distance_from_letters):
		distance_past_border = distance_from_letters - self.dither_start_distance
		closeness_to_edge = np.clip(distance_past_border / self.dither_width, 0.0, 1.0)
		return self.strength * closeness_to_edge ** self.falloff_power

	def _distance_from_letters(self, grid_size):
		distance = np.full(grid_size, np.inf, dtype=np.float32)
		reach = self.line_width / 2 + self.clear_border + self.dither_width
		for outline in self.outlines:
			for segment in outline.segments:
				self._measure_segment(distance, segment, reach)
		return distance

	def _measure_segment(self, distance, segment, reach):
		grid_width, grid_height = distance.shape
		start_x, start_y = segment.start
		end_x, end_y = segment.end
		left = max(0, int((min(start_x, end_x) - reach) / self.dither.cell))
		right = min(grid_width, int((max(start_x, end_x) + reach) / self.dither.cell) + 2)
		top = max(0, int((min(start_y, end_y) - reach) / self.dither.cell))
		bottom = min(grid_height, int((max(start_y, end_y) + reach) / self.dither.cell) + 2)
		if left >= right or top >= bottom:
			return
		cell_columns, cell_rows = np.mgrid[left:right, top:bottom].astype(np.float32)
		columns = (cell_columns + 0.5) * self.dither.cell
		rows = (cell_rows + 0.5) * self.dither.cell
		run_x, run_y = end_x - start_x, end_y - start_y
		along = np.clip(((columns - start_x) * run_x + (rows - start_y) * run_y)
		                / max(1e-6, run_x * run_x + run_y * run_y), 0.0, 1.0)
		segment_distance = np.hypot(columns - (start_x + along * run_x), rows - (start_y + along * run_y))
		region = distance[left:right, top:bottom]
		np.minimum(region, segment_distance, out=region)

	def _outside_letters(self, distance_from_letters):
		free_cells = distance_from_letters > self.line_width / 2 + self.dither.cell
		free_surface = pygame.Surface(free_cells.shape, pygame.SRCALPHA)
		alpha = pygame.surfarray.pixels_alpha(free_surface)
		alpha[free_cells] = 255
		del alpha
		outside = pygame.mask.from_surface(free_surface, 1).connected_component((0, 0))
		outside_surface = outside.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
		return pygame.surfarray.array_alpha(outside_surface) > 0


class DitherSpreadOrderMap:

	def __init__(self, frame):
		self.frame = frame

	def build(self, surface):
		cell_order = self.frame.spread_needed_by_cells()
		pixel_order = self.frame.dither.enlarged(cell_order, surface.get_size())
		return (pixel_order.T * 255.0).astype(np.uint8)
