import math


class LineSegment:

	def __init__(self, start, end, length_before):
		self.start = start
		self.end = end
		self.length_before = length_before
		self.length = math.dist(start, end)

	@property
	def length_after(self):
		return self.length_before + self.length
