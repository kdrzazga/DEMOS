import math

import numpy as np
from OpenGL.GL import *


class SwayingSurface:

	def __init__(self, width, height, columns=72, rows=44):
		self.width = width
		self.height = height
		self.yaw_amplitude_degrees = 18.0
		self.yaw_speed = 0.42
		self.pitch_amplitude_degrees = 6.0
		self.pitch_speed = 0.31
		self.wave_amplitude = 0.09
		self.wave_length = 2.6
		self.wave_speed = 1.4
		self.light_direction = np.array([0.35, 0.45, 0.82], dtype=np.float32)
		self.light_direction /= np.linalg.norm(self.light_direction)
		self.ambient = 0.55
		self.diffuse = 0.5
		self.yaw_degrees = 0.0
		self.pitch_degrees = 0.0
		u, v = np.meshgrid(np.linspace(0.0, 1.0, columns + 1, dtype=np.float32),
		                   np.linspace(0.0, 1.0, rows + 1, dtype=np.float32))
		self.base_x = ((u - 0.5) * width).ravel()
		self.base_y = ((v - 0.5) * height).ravel()
		self.texture_points = np.ascontiguousarray(np.stack([u.ravel(), v.ravel()], axis=1))
		self.indices = self._triangle_indices(columns, rows)
		self.vertices = np.zeros((self.base_x.size, 3), dtype=np.float32)
		self.colors = np.ones((self.base_x.size, 4), dtype=np.float32)

	@staticmethod
	def _triangle_indices(columns, rows):
		stride = columns + 1
		row_index, column_index = np.mgrid[0:rows, 0:columns]
		corner = (row_index * stride + column_index).ravel()
		quads = np.stack([corner, corner + 1, corner + stride + 1,
		                  corner, corner + stride + 1, corner + stride], axis=1)
		return np.ascontiguousarray(quads.ravel().astype(np.uint32))

	def update(self, seconds):
		phase = self.base_x / self.wave_length * 2 * math.pi - seconds * self.wave_speed
		ripple = self.base_y / self.wave_length * math.pi + seconds * self.wave_speed * 0.7
		depth = self.wave_amplitude * (np.sin(phase) + 0.35 * np.sin(ripple))
		slope_x = self.wave_amplitude * np.cos(phase) * 2 * math.pi / self.wave_length
		slope_y = self.wave_amplitude * 0.35 * np.cos(ripple) * math.pi / self.wave_length
		normals = np.stack([-slope_x, -slope_y, np.ones_like(slope_x)], axis=1)
		normals /= np.linalg.norm(normals, axis=1, keepdims=True)
		shade = self.ambient + self.diffuse * np.clip(normals @ self.light_direction, 0.0, 1.0)
		self.vertices[:, 0] = self.base_x
		self.vertices[:, 1] = self.base_y
		self.vertices[:, 2] = depth
		self.colors[:, 0] = shade
		self.colors[:, 1] = shade
		self.colors[:, 2] = shade
		self.yaw_degrees = self.yaw_amplitude_degrees * math.sin(seconds * self.yaw_speed)
		self.pitch_degrees = self.pitch_amplitude_degrees * math.sin(seconds * self.pitch_speed + 1.0)

	def _draw_mesh(self):
		glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, self.indices)

	def render(self, graffiti_texture):
		glPushMatrix()
		glRotatef(self.pitch_degrees, 1.0, 0.0, 0.0)
		glRotatef(self.yaw_degrees, 0.0, 1.0, 0.0)
		glEnable(GL_TEXTURE_2D)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
		glEnableClientState(GL_VERTEX_ARRAY)
		glEnableClientState(GL_TEXTURE_COORD_ARRAY)
		glEnableClientState(GL_COLOR_ARRAY)
		glVertexPointer(3, GL_FLOAT, 0, self.vertices)
		glTexCoordPointer(2, GL_FLOAT, 0, self.texture_points)
		glColorPointer(4, GL_FLOAT, 0, self.colors)
		glEnable(GL_BLEND)
		glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		glDepthMask(GL_FALSE)
		glBindTexture(GL_TEXTURE_2D, graffiti_texture)
		self._draw_mesh()
		glDepthMask(GL_TRUE)
		glDisableClientState(GL_COLOR_ARRAY)
		glDisableClientState(GL_TEXTURE_COORD_ARRAY)
		glDisableClientState(GL_VERTEX_ARRAY)
		glPopMatrix()
