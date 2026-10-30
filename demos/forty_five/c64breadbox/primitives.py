import math

from OpenGL.GL import *

from demos.forty_five.geometry import color, quad


class Box:

	def __init__(self, minimum, maximum):
		self.minimum = minimum
		self.maximum = maximum

	def _faces(self):
		x0, y0, z0 = self.minimum
		x1, y1, z1 = self.maximum
		return {
			"top": ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)),
			"bottom": ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),
			"front": ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
			"back": ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)),
			"left": ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)),
			"right": ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)),
		}

	def draw(self, rgb, skip=()):
		color(rgb)
		glBegin(GL_QUADS)
		for name, corners in self._faces().items():
			if name not in skip:
				quad(*corners)
		glEnd()

	def draw_photo_top(self, photo):
		photo.begin()
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for corner in self._faces()["top"]:
			photo.vertex(*corner)
		glEnd()
		photo.end()


class Cylinder:

	def __init__(self, centre, radius, length, axis, segments=32):
		self.centre = centre
		self.radius = radius
		self.length = length
		self.axis = axis
		self.segments = segments

	def _point(self, along, angle, radius):
		centre_x, centre_y, centre_z = self.centre
		across, up = radius * math.cos(angle), radius * math.sin(angle)
		if self.axis == "x":
			return centre_x + along, centre_y + up, centre_z + across
		if self.axis == "z":
			return centre_x + across, centre_y + up, centre_z + along
		return centre_x + across, centre_y + along, centre_z + up

	def _normal(self, angle):
		across, up = math.cos(angle), math.sin(angle)
		if self.axis == "x":
			return 0.0, up, across
		if self.axis == "z":
			return across, up, 0.0
		return across, 0.0, up

	def _axis_vector(self):
		return {"x": (1.0, 0.0, 0.0), "z": (0.0, 0.0, 1.0)}.get(self.axis, (0.0, 1.0, 0.0))

	def _angles(self):
		return [2.0 * math.pi * index / self.segments for index in range(self.segments + 1)]

	def draw(self, rgb=None, alpha=1.0, photo=None, caps=True):
		if photo is not None:
			photo.begin()
			emit = photo.vertex
		else:
			glColor4f(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, alpha)
			emit = glVertex3f
		half_length = self.length / 2
		glBegin(GL_QUAD_STRIP)
		for angle in self._angles():
			glNormal3f(*self._normal(angle))
			emit(*self._point(-half_length, angle, self.radius))
			emit(*self._point(half_length, angle, self.radius))
		glEnd()
		if caps:
			axis_x, axis_y, axis_z = self._axis_vector()
			for along, sign in ((-half_length, -1.0), (half_length, 1.0)):
				glBegin(GL_TRIANGLE_FAN)
				glNormal3f(axis_x * sign, axis_y * sign, axis_z * sign)
				emit(*self._point(along, 0.0, 0.0))
				for angle in self._angles():
					emit(*self._point(along, angle, self.radius))
				glEnd()
		if photo is not None:
			photo.end()
