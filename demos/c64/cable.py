"""A peripheral's lead: a smooth tube through world points, a strain-relief
grommet where it leaves the case and a plug at the far end.

``Cable`` draws the tube and the grommet; each peripheral subclasses it and
draws its own plug in ``_draw_plug(entry, forward)``. ``_plug_frame`` gives the
plug a frame lying flat on the floor, pointing along the last stretch of lead,
scaled by ``plug_scale`` so one plug design can be drawn at any size.
"""

import math

from OpenGL.GL import *

from demos.c64.geometry import color, face_normal


class Cable:

	def __init__(self, path, radius, cable_color, grommet_color, grommet_radius, grommet_length, plug_scale=1.0):
		self.path = path
		self.radius = radius
		self.cable_color = cable_color
		self.grommet_color = grommet_color
		self.grommet_radius = grommet_radius
		self.grommet_length = grommet_length
		self.plug_scale = plug_scale
		self.samples_per_span = 10
		self.ring_segments = 12
		self._display_list = None

	def build(self):
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		points = self._smooth_path()
		color(self.cable_color)
		self._tube(points, self.radius)
		color(self.grommet_color)
		self._tube(self._grommet_points(points), self.grommet_radius)
		self._draw_plug(points[-1], self._direction(points[-2], points[-1]))
		glEndList()

	def _draw_plug(self, entry, forward):
		"""Draw the plug whose back face takes the lead at `entry`. Override."""

	def _smooth_path(self):
		"""Catmull-Rom spline through the path points."""
		padded = (self.path[0],) + tuple(self.path) + (self.path[-1],)
		points = []
		for span in range(len(self.path) - 1):
			p0, p1, p2, p3 = padded[span:span + 4]
			for step in range(self.samples_per_span):
				t = step / self.samples_per_span
				points.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t
				                           + (3 * b - a - 3 * c + d) * t * t * t)
				                    for a, b, c, d in zip(p0, p1, p2, p3)))
		points.append(tuple(self.path[-1]))
		return points

	def _grommet_points(self, points):
		travelled, kept = 0.0, [points[0]]
		for previous, current in zip(points, points[1:]):
			travelled += math.dist(previous, current)
			kept.append(current)
			if travelled >= self.grommet_length:
				break
		return kept

	@staticmethod
	def _direction(start, end):
		length = math.dist(start, end) or 1.0
		return tuple((e - s) / length for s, e in zip(start, end))

	@staticmethod
	def _cross(u, v):
		return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])

	@staticmethod
	def _normalized(v):
		length = math.sqrt(sum(c * c for c in v)) or 1.0
		return tuple(c / length for c in v)

	def _plug_frame(self, entry, forward):
		"""point(along, across, height) in a frame standing on the floor under
		`entry`: along the lead's last direction (flattened), across to its side, up;
		all three are multiplied by plug_scale."""
		flat_forward = self._normalized((forward[0], 0.0, forward[2]))
		side = self._normalized(self._cross((0.0, 1.0, 0.0), flat_forward))
		up = (0.0, 1.0, 0.0)
		base = (entry[0], 0.0, entry[2])

		scale = self.plug_scale

		def point(along, across, height):
			return tuple(b + scale * (along * f + across * s + height * u)
			             for b, f, s, u in zip(base, flat_forward, side, up))

		return point

	def _tube(self, points, radius):
		"""Rings around the path using parallel-transported frames, joined with
		smooth-shaded quads wound so that their front faces look outward."""
		rings = []
		normal = None
		for index, centre in enumerate(points):
			tangent = self._direction(points[max(index - 1, 0)], points[min(index + 1, len(points) - 1)])
			if normal is None:
				reference = (0.0, 1.0, 0.0) if abs(tangent[1]) < 0.9 else (1.0, 0.0, 0.0)
				normal = self._normalized(self._cross(tangent, reference))
			else:
				along = sum(n * t for n, t in zip(normal, tangent))
				normal = self._normalized(tuple(n - along * t for n, t in zip(normal, tangent)))
			binormal = self._cross(tangent, normal)
			ring = []
			for segment in range(self.ring_segments):
				angle = 2 * math.pi * segment / self.ring_segments
				outward = tuple(math.cos(angle) * n + math.sin(angle) * b for n, b in zip(normal, binormal))
				ring.append((tuple(c + radius * o for c, o in zip(centre, outward)), outward))
			rings.append(ring)

		glBegin(GL_QUADS)
		for ring, next_ring in zip(rings, rings[1:]):
			for segment in range(self.ring_segments):
				following = (segment + 1) % self.ring_segments
				corners = [ring[segment], ring[following], next_ring[following], next_ring[segment]]
				winding = face_normal(corners[0][0], corners[1][0], corners[2][0])
				if sum(w * o for w, o in zip(winding, corners[0][1])) < 0:
					corners.reverse()
				for position, outward in corners:
					glNormal3f(*outward)
					glVertex3f(*position)
		glEnd()
		for end_ring in (rings[0], rings[-1]):
			glBegin(GL_POLYGON)
			glNormal3f(*face_normal(end_ring[0][0], end_ring[1][0], end_ring[2][0]))
			for position, _ in end_ring:
				glVertex3f(*position)
			glEnd()

	def draw(self):
		glCallList(self._display_list)

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)
