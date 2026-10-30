import math

import numpy as np
from OpenGL.GL import *

from demos.c64.rotation import rotation_x, rotation_y


class OrbitCamera:

	def __init__(self, field_of_view_degrees, aspect_ratio, yaw_degrees=0.0, pitch_degrees=0.0, distance=50.0):
		self.field_of_view_degrees = field_of_view_degrees
		self.aspect_ratio = aspect_ratio
		self.yaw_degrees = yaw_degrees
		self.pitch_degrees = pitch_degrees
		self.distance = distance

	def apply(self):
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.distance)
		glRotatef(self.pitch_degrees, 1.0, 0.0, 0.0)
		glRotatef(self.yaw_degrees, 0.0, 1.0, 0.0)

	def world_to_eye_rotation(self):
		return rotation_x(self.pitch_degrees) @ rotation_y(self.yaw_degrees)

	def eye_to_world(self, eye_position, eye_rotation):
		inverse_rotation = self.world_to_eye_rotation().T
		world_position = inverse_rotation @ (np.asarray(eye_position) + np.array((0.0, 0.0, self.distance)))
		return world_position, inverse_rotation @ eye_rotation

	def view_point(self, fraction_x, fraction_y, depth):
		half_height = depth * math.tan(math.radians(self.field_of_view_degrees) / 2)
		return np.array((fraction_x * half_height * self.aspect_ratio, fraction_y * half_height, -depth))
