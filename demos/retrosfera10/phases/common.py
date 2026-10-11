from OpenGL.GL import (
	GL_AMBIENT, GL_DIFFUSE, GL_LIGHT0, GL_MODELVIEW, GL_POSITION, GL_PROJECTION, glLightfv, glLoadIdentity,
	glMatrixMode,
)
from OpenGL.GLU import gluLookAt, gluPerspective


class Easing:
	@staticmethod
	def clamp(value):
		return max(0.0, min(1.0, value))

	@staticmethod
	def smooth(value):
		value = Easing.clamp(value)
		return value * value * (3.0 - 2.0 * value)

	@staticmethod
	def blend(start, end, factor):
		return start + (end - start) * factor

	@staticmethod
	def curve(start, bend, end, factor):
		return Easing.blend(Easing.blend(start, bend, factor), Easing.blend(bend, end, factor), factor)


class GeoPoint:
	def __init__(self, latitude, longitude):
		self.latitude = latitude
		self.longitude = longitude


class PhaseCursor:
	def __init__(self, time):
		self.time = time
		self.start = 0.0

	def advance(self, duration):
		progress = Easing.clamp((self.time - self.start) / duration)
		self.start += duration
		return progress

	def finished(self):
		return self.time >= self.start


class Light:
	def __init__(self, direction, ambient, diffuse):
		self.direction = direction.normalized()
		self.ambient = ambient
		self.diffuse = diffuse

	def apply(self):
		glLightfv(GL_LIGHT0, GL_AMBIENT, self.ambient)
		glLightfv(GL_LIGHT0, GL_DIFFUSE, self.diffuse)
		glLightfv(GL_LIGHT0, GL_POSITION, (self.direction.x, self.direction.y, self.direction.z, 0.0))

	def brightness(self, normal):
		lit = max(0.0, normal.dot(self.direction))
		return min(1.0, self.ambient[0] + self.diffuse[0] * lit)


class Camera:
	def __init__(self, screen_width, screen_height, field_of_view=45.0):
		self.screen_width = screen_width
		self.screen_height = screen_height
		self.field_of_view = field_of_view

	def apply_projection(self, near, far):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(self.field_of_view, self.screen_width / self.screen_height, near, far)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def look(self, eye, target, up):
		gluLookAt(eye.x, eye.y, eye.z, target.x, target.y, target.z, up.x, up.y, up.z)


class Handover:
	def __init__(self, earth_texture_id, surface_brightness, altitude_degrees):
		self.earth_texture_id = earth_texture_id
		self.surface_brightness = surface_brightness
		self.altitude_degrees = altitude_degrees


class Phase:
	def __init__(self, camera):
		self.camera = camera
		self.elapsed = 0.0
		self.done = False

	def begin(self, handover):
		self.elapsed = 0.0

	def update(self, seconds):
		self.elapsed += seconds

	def render(self):
		raise NotImplementedError

	def handover(self):
		return None
