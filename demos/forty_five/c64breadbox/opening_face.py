from OpenGL.GL import *

from demos.forty_five.geometry import color, quad


class OpeningFace:

	def __init__(self, start, end, bottom, top_points, openings, to_world, outward_normal):
		self.start = start
		self.end = end
		self.bottom = bottom
		self.top_points = tuple(sorted(top_points))
		self.openings = tuple(opening for opening in openings
		                      if opening.end > start and opening.start < end and opening.top > bottom)
		self.to_world = to_world
		self.outward_normal = outward_normal

	def top_at(self, along):
		points = self.top_points
		if along <= points[0][0]:
			return points[0][1]
		for (along_0, top_0), (along_1, top_1) in zip(points, points[1:]):
			if along <= along_1:
				share = (along - along_0) / (along_1 - along_0) if along_1 > along_0 else 1.0
				return top_0 + (top_1 - top_0) * share
		return points[-1][1]

	def _is_open(self, along, up):
		return any(opening.start < along < opening.end and opening.bottom < up < opening.top
		           for opening in self.openings)

	def _along_splits(self):
		edges = {self.start, self.end}
		edges.update(along for along, _ in self.top_points if self.start < along < self.end)
		for opening in self.openings:
			edges.update(edge for edge in (opening.start, opening.end) if self.start < edge < self.end)
		return sorted(edges)

	def _up_splits(self, lowest_top):
		edges = {self.bottom}
		for opening in self.openings:
			edges.update(edge for edge in (opening.bottom, opening.top) if self.bottom < edge < lowest_top)
		return sorted(edges)

	def _emit(self, corners):
		glNormal3f(*self.outward_normal)
		for along, up in corners:
			glVertex3f(*self.to_world(along, up))

	def draw(self, rgb, shade=1.0):
		color(rgb, shade)
		glBegin(GL_QUADS)
		along_splits = self._along_splits()
		for along_0, along_1 in zip(along_splits, along_splits[1:]):
			top_0, top_1 = self.top_at(along_0), self.top_at(along_1)
			up_splits = self._up_splits(min(top_0, top_1))
			middle_along = (along_0 + along_1) / 2
			for index, up_0 in enumerate(up_splits):
				is_highest = index == len(up_splits) - 1
				up_1_start = top_0 if is_highest else up_splits[index + 1]
				up_1_end = top_1 if is_highest else up_splits[index + 1]
				middle_up = (up_0 + (up_1_start + up_1_end) / 2) / 2
				if self._is_open(middle_along, middle_up):
					continue
				self._emit(((along_0, up_0), (along_1, up_0), (along_1, up_1_end), (along_0, up_1_start)))
		glEnd()

	def draw_tunnels(self, inward, depth, rgb, shade=0.7):
		color(rgb, shade)
		glBegin(GL_QUADS)
		for opening in self.openings:
			start, end = max(opening.start, self.start), min(opening.end, self.end)
			bottom = max(opening.bottom, self.bottom)
			top = min(opening.top, self.top_at(start), self.top_at(end))
			sides = [((start, bottom), (start, top)), ((end, top), (end, bottom))]
			if opening.bottom > self.bottom:
				sides.append(((end, bottom), (start, bottom)))
			if opening.top < min(self.top_at(start), self.top_at(end)):
				sides.append(((start, top), (end, top)))
			for (along_0, up_0), (along_1, up_1) in sides:
				outer_0, outer_1 = self.to_world(along_0, up_0), self.to_world(along_1, up_1)
				inner_0 = tuple(coordinate + direction * depth for coordinate, direction in zip(outer_0, inward))
				inner_1 = tuple(coordinate + direction * depth for coordinate, direction in zip(outer_1, inward))
				quad(outer_0, outer_1, inner_1, inner_0)
		glEnd()
