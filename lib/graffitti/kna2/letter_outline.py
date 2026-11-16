from lib.graffitti.kna2.line_segment import LineSegment


class LetterOutline:

	def __init__(self, name, strokes):
		self.name = name
		self.strokes = [[(float(x), float(y)) for x, y in stroke] for stroke in strokes]
		self.segments = self._cut_into_segments()

	def _cut_into_segments(self):
		segments = []
		drawn_length = 0.0
		for stroke in self.strokes:
			for start, end in zip(stroke, stroke[1:]):
				segment = LineSegment(start, end, drawn_length)
				segments.append(segment)
				drawn_length = segment.length_after
		return segments

	@property
	def total_length(self):
		return self.segments[-1].length_after

	@property
	def bounds(self):
		xs = [x for stroke in self.strokes for x, _ in stroke]
		ys = [y for stroke in self.strokes for _, y in stroke]
		return min(xs), min(ys), max(xs), max(ys)

	def transformed(self, scale, shift_x, shift_y):
		return LetterOutline(self.name, [[(x * scale + shift_x, y * scale + shift_y) for x, y in stroke]
		                                 for stroke in self.strokes])
