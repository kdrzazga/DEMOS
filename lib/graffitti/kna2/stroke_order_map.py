import numpy as np


class StrokeOrderMap:

	def __init__(self, outline, line_width):
		self.outline = outline
		self.reach = line_width / 2 + 2.0

	def build(self, surface):
		width, height = surface.get_size()
		order = np.ones((height, width), dtype=np.float32)
		for segment in self.outline.segments:
			self._stamp(order, segment)
		return (order * 255.0).astype(np.uint8)

	def _stamp(self, order, segment):
		height, width = order.shape
		start_x, start_y = segment.start
		end_x, end_y = segment.end
		left = max(0, int(min(start_x, end_x) - self.reach))
		right = min(width, int(max(start_x, end_x) + self.reach) + 2)
		top = max(0, int(min(start_y, end_y) - self.reach))
		bottom = min(height, int(max(start_y, end_y) + self.reach) + 2)
		if left >= right or top >= bottom:
			return
		rows, columns = np.mgrid[top:bottom, left:right].astype(np.float32) + 0.5
		run_x, run_y = end_x - start_x, end_y - start_y
		along = np.clip(((columns - start_x) * run_x + (rows - start_y) * run_y)
		                / max(1e-6, run_x * run_x + run_y * run_y), 0.0, 1.0)
		distance = np.hypot(columns - (start_x + along * run_x), rows - (start_y + along * run_y))
		painted_at = (segment.length_before + along * segment.length) / self.outline.total_length
		region = order[top:bottom, left:right]
		np.minimum(region, np.where(distance <= self.reach, painted_at, 1.0), out=region)
