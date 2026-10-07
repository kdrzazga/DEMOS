"""Ring-stack surfaces: a solid described as a column of closed horizontal
outlines ("rings"), each with the same number of points, joined band by band.

Outlines are lists of (x, z) points; rings are lists of (x, y, z) points.
Faces are oriented outward from each ring's centroid, so outlines may run in
either direction as long as every ring of one surface runs the same way.
"""

import math

from OpenGL.GL import *


def rounded_rect_outline(half_width, half_depth, radius, corner_segments=8, centre=(0.0, 0.0)):
	"""Rounded rectangle as (x, z) points, corner by corner."""
	centre_x, centre_z = centre
	radius = max(0.0, min(radius, half_width, half_depth))
	points = []
	for corner_x, corner_z, start_degrees in ((half_width - radius, half_depth - radius, 0),
	                                          (-half_width + radius, half_depth - radius, 90),
	                                          (-half_width + radius, -half_depth + radius, 180),
	                                          (half_width - radius, -half_depth + radius, 270)):
		for step in range(corner_segments + 1):
			angle = math.radians(start_degrees + 90 * step / corner_segments)
			points.append((centre_x + corner_x + radius * math.cos(angle),
			               centre_z + corner_z + radius * math.sin(angle)))
	return points


def circle_outline(radius, segments=24, centre=(0.0, 0.0)):
	return [(centre[0] + radius * math.cos(2 * math.pi * step / segments),
	         centre[1] + radius * math.sin(2 * math.pi * step / segments)) for step in range(segments)]


def superellipse_outline(half_width, front, back, segments=28, exponent=2.6, centre_z=0.0):
	"""Squarish oval: half_width to the sides, `front` toward +z and `back`
	toward -z; exponent 2 is an ellipse, larger values are boxier."""
	points = []
	for step in range(segments):
		angle = 2 * math.pi * step / segments
		cosine, sine = math.cos(angle), math.sin(angle)
		x = half_width * math.copysign(abs(cosine) ** (2 / exponent), cosine)
		z = (front if sine > 0 else back) * math.copysign(abs(sine) ** (2 / exponent), sine)
		points.append((x, centre_z + z))
	return points


def ring(outline, y):
	return [(x, y, z) for x, z in outline]


def _centroid(points):
	count = len(points)
	return tuple(sum(point[axis] for point in points) / count for axis in range(3))


def _subtract(a, b):
	return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _cross(u, v):
	return u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]


def _dot(u, v):
	return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _normalized(v):
	length = math.sqrt(_dot(v, v))
	return None if length < 1e-9 else (v[0] / length, v[1] / length, v[2] / length)


def draw_ring_surface(rings, smooth=False):
	"""Join consecutive rings with quads. Flat faces take their normal from the
	quad's diagonals; smooth ones get per-corner normals from the neighbouring
	points along the ring and up the column."""
	centres = [_centroid(points) for points in rings]
	count = len(rings[0])

	def corner_normal(level, index):
		along = _subtract(rings[level][(index + 1) % count], rings[level][index - 1])
		up = _subtract(rings[min(level + 1, len(rings) - 1)][index], rings[max(level - 1, 0)][index])
		normal = _normalized(_cross(along, up))
		if normal is None:
			return None
		outward = _subtract(rings[level][index], centres[level])
		return normal if _dot(normal, outward) >= 0 else tuple(-c for c in normal)

	glBegin(GL_QUADS)
	for level in range(len(rings) - 1):
		for index in range(count):
			following = (index + 1) % count
			corners = [(level, index), (level, following), (level + 1, following), (level + 1, index)]
			points = [rings[l][i] for l, i in corners]
			face = _normalized(_cross(_subtract(points[2], points[0]), _subtract(points[3], points[1])))
			if face is None:
				continue
			middle = _centroid(points)
			axis = _centroid((centres[level], centres[level + 1]))
			if _dot(face, _subtract(middle, axis)) < 0:
				corners.reverse()
				points.reverse()
				face = tuple(-c for c in face)
			for (l, i), point in zip(corners, points):
				glNormal3f(*((corner_normal(l, i) or face) if smooth else face))
				glVertex3f(*point)
	glEnd()


def draw_cap(points, facing_up):
	"""Close a convex ring with a flat polygon facing up or down."""
	signed_area = sum(x0 * z1 - x1 * z0 for (x0, _, z0), (x1, _, z1) in zip(points, points[1:] + points[:1]))
	if (signed_area < 0) != facing_up:
		points = points[::-1]
	glBegin(GL_POLYGON)
	glNormal3f(0.0, 1.0 if facing_up else -1.0, 0.0)
	for point in points:
		glVertex3f(*point)
	glEnd()
