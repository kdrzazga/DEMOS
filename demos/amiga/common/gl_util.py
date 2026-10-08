"""Small PyOpenGL helpers: shader programs, VAO meshes, textures and row-major matrices.

Matrices are numpy row-major; they are uploaded with transpose=GL_TRUE.
"""
import ctypes
import math

import numpy as np
from OpenGL.GL import *


class ShaderProgram:

	def __init__(self, vertex_src, fragment_src):
		self.handle = glCreateProgram()
		shaders = [self._compile(GL_VERTEX_SHADER, vertex_src), self._compile(GL_FRAGMENT_SHADER, fragment_src)]
		for shader in shaders:
			glAttachShader(self.handle, shader)
		glLinkProgram(self.handle)
		if not glGetProgramiv(self.handle, GL_LINK_STATUS):
			raise RuntimeError("Shader link failed:\n" + glGetProgramInfoLog(self.handle).decode(errors="replace"))
		for shader in shaders:
			glDeleteShader(shader)
		self._locations = {}

	@staticmethod
	def _compile(kind, source):
		shader = glCreateShader(kind)
		glShaderSource(shader, source)
		glCompileShader(shader)
		if not glGetShaderiv(shader, GL_COMPILE_STATUS):
			kind_name = "vertex" if kind == GL_VERTEX_SHADER else "fragment"
			raise RuntimeError(f"{kind_name} shader compile failed:\n" + glGetShaderInfoLog(shader).decode(errors="replace"))
		return shader

	def use(self):
		glUseProgram(self.handle)

	def _location(self, name):
		if name not in self._locations:
			self._locations[name] = glGetUniformLocation(self.handle, name)
		return self._locations[name]

	def set_int(self, name, value):
		glUniform1i(self._location(name), int(value))

	def set_float(self, name, value):
		glUniform1f(self._location(name), float(value))

	def set_vec2(self, name, x, y):
		glUniform2f(self._location(name), float(x), float(y))

	def set_vec3(self, name, x, y, z):
		glUniform3f(self._location(name), float(x), float(y), float(z))

	def set_vec2_array(self, name, values):
		data = np.asarray(values, dtype=np.float32).reshape(-1, 2)
		if len(data):
			glUniform2fv(self._location(name), len(data), data)

	def set_vec4_array(self, name, values):
		data = np.asarray(values, dtype=np.float32).reshape(-1, 4)
		if len(data):
			glUniform4fv(self._location(name), len(data), data)

	def set_mat3(self, name, matrix):
		glUniformMatrix3fv(self._location(name), 1, GL_TRUE, np.asarray(matrix, dtype=np.float32))

	def set_mat4(self, name, matrix):
		glUniformMatrix4fv(self._location(name), 1, GL_TRUE, np.asarray(matrix, dtype=np.float32))


class Mesh:
	"""Interleaved float32 vertex buffer in a VAO. `layout` is ((location, component_count), ...)."""

	def __init__(self, vertices, layout, mode):
		self.mode = mode
		vertices = np.ascontiguousarray(vertices, dtype=np.float32)
		floats_per_vertex = sum(count for _, count in layout)
		self.vertex_count = vertices.size // floats_per_vertex
		self.vao = glGenVertexArrays(1)
		self.vbo = glGenBuffers(1)
		glBindVertexArray(self.vao)
		glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
		glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
		stride = floats_per_vertex * 4
		offset = 0
		for location, count in layout:
			glEnableVertexAttribArray(location)
			glVertexAttribPointer(location, count, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
			offset += count * 4
		glBindVertexArray(0)

	def draw(self):
		glBindVertexArray(self.vao)
		glDrawArrays(self.mode, 0, self.vertex_count)
		glBindVertexArray(0)


def unit_quad_mesh():
	"""Two triangles covering 0..1 with matching uv (location 0 = pos, 1 = uv)."""
	corners = ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))
	vertices = [value for x, y in corners for value in (x, y, x, y)]
	return Mesh(vertices, ((0, 2), (1, 2)), GL_TRIANGLES)


def upload_rgba_texture(rgba):
	"""rgba: uint8 array (h, w, 4), row 0 = bottom (GL convention). Mipmapped, clamped."""
	height, width = rgba.shape[:2]
	texture = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, texture)
	glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, np.ascontiguousarray(rgba))
	glGenerateMipmap(GL_TEXTURE_2D)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	return texture


def perspective(fov_y, aspect, near, far):
	focal = 1.0 / math.tan(fov_y / 2.0)
	matrix = np.zeros((4, 4), dtype=np.float32)
	matrix[0, 0] = focal / aspect
	matrix[1, 1] = focal
	matrix[2, 2] = (far + near) / (near - far)
	matrix[2, 3] = (2.0 * far * near) / (near - far)
	matrix[3, 2] = -1.0
	return matrix


def translate(x, y, z):
	matrix = np.identity(4, dtype=np.float32)
	matrix[0, 3], matrix[1, 3], matrix[2, 3] = x, y, z
	return matrix


def scale(x, y, z):
	return np.diag((x, y, z, 1.0)).astype(np.float32)


def rotate_x(angle):
	cos_a, sin_a = math.cos(angle), math.sin(angle)
	matrix = np.identity(4, dtype=np.float32)
	matrix[1, 1], matrix[1, 2] = cos_a, -sin_a
	matrix[2, 1], matrix[2, 2] = sin_a, cos_a
	return matrix


def rotate_y(angle):
	cos_a, sin_a = math.cos(angle), math.sin(angle)
	matrix = np.identity(4, dtype=np.float32)
	matrix[0, 0], matrix[0, 2] = cos_a, sin_a
	matrix[2, 0], matrix[2, 2] = -sin_a, cos_a
	return matrix


def rotate_z(angle):
	cos_a, sin_a = math.cos(angle), math.sin(angle)
	matrix = np.identity(4, dtype=np.float32)
	matrix[0, 0], matrix[0, 1] = cos_a, -sin_a
	matrix[1, 0], matrix[1, 1] = sin_a, cos_a
	return matrix


def clamp01(value):
	return max(0.0, min(1.0, value))


def ease_out_cubic(progress):
	return 1.0 - (1.0 - clamp01(progress)) ** 3


def smoothstep(edge0, edge1, value):
	progress = clamp01((value - edge0) / (edge1 - edge0))
	return progress * progress * (3.0 - 2.0 * progress)
