"""Flat-coloured, simply lit meshes built from boxes and extruded convex polygons.

Vertex layout: position (3), normal (3), colour (3). Builders return flat float lists so several
parts can be concatenated into one Mesh.
"""
import numpy as np
from OpenGL.GL import *

from demos.amiga.common import glsl
from demos.amiga.common.gl_util import Mesh, ShaderProgram

COLORED_LAYOUT = ((0, 3), (1, 3), (2, 3))


def _emit(triangles, points, normal, colors):
	for index in range(1, len(points) - 1):
		for corner in (0, index, index + 1):
			triangles.extend((*points[corner], *normal, *colors[corner]))


def box_triangles(min_corner, max_corner, color, face_colors=None):
	"""Axis-aligned box. `face_colors` may override faces by name: front back left right top bottom."""
	(x0, y0, z0), (x1, y1, z1) = min_corner, max_corner
	faces = {
		"front": (((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)), (0, 0, 1)),
		"back": (((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)), (0, 0, -1)),
		"left": (((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)), (-1, 0, 0)),
		"right": (((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)), (1, 0, 0)),
		"top": (((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)), (0, 1, 0)),
		"bottom": (((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)), (0, -1, 0)),
	}
	face_colors = face_colors or {}
	triangles = []
	for name, (points, normal) in faces.items():
		face_color = face_colors.get(name, color)
		_emit(triangles, points, normal, [face_color] * 4)
	return triangles


def extruded_polygon_triangles(points, z_front, z_back, color_at):
	"""Convex polygon in XY (counter-clockwise), extruded between z_back and z_front.
	`color_at(x, y)` gives the vertex colour, so gradients follow the shape."""
	front = [(x, y, z_front) for x, y in points]
	back = [(x, y, z_back) for x, y in points]
	colors = [color_at(x, y) for x, y in points]
	triangles = []
	_emit(triangles, front, (0, 0, 1), colors)
	_emit(triangles, back[::-1], (0, 0, -1), colors[::-1])
	for index, (x0, y0) in enumerate(points):
		x1, y1 = points[(index + 1) % len(points)]
		edge = np.array((x1 - x0, y1 - y0))
		normal = (edge[1], -edge[0], 0.0) / np.linalg.norm(edge)
		side = [back[index], back[(index + 1) % len(points)], front[(index + 1) % len(points)], front[index]]
		next_color = colors[(index + 1) % len(points)]
		_emit(triangles, side, tuple(normal), [colors[index], next_color, next_color, colors[index]])
	return triangles


def colored_mesh(triangles):
	return Mesh(triangles, COLORED_LAYOUT, GL_TRIANGLES)


class ColoredMeshRenderer:
	"""Lights flat-coloured meshes; front faces facing the camera keep (almost) their palette colour."""

	def __init__(self, to_light=(-0.25, 0.35, 0.9), shadow_level=0.55):
		direction = np.asarray(to_light, dtype=np.float32)
		self.to_light = direction / np.linalg.norm(direction)
		self.shadow_level = shadow_level
		self.program = ShaderProgram(glsl.COLORED_MESH_VERTEX, glsl.COLORED_MESH_FRAGMENT)

	def begin(self):
		self.program.use()
		self.program.set_vec3("u_to_light", *self.to_light)
		self.program.set_float("u_shadow_level", self.shadow_level)
		glBlendFunc(GL_ONE, GL_ZERO)

	def draw(self, mesh, model, view_projection, alpha=1.0):
		"""`model` must be rotation + translation only."""
		self.program.set_mat4("u_mvp", view_projection @ model)
		self.program.set_mat3("u_normal_matrix", model[:3, :3])
		self.program.set_float("u_alpha", alpha)
		mesh.draw()


def translated(triangles, offset):
	"""Shift a flat triangle list (COLORED_LAYOUT) by offset (x, y, z)."""
	stride = sum(count for _, count in COLORED_LAYOUT)
	values = np.asarray(triangles, dtype=np.float32).reshape(-1, stride)
	values[:, :3] += np.asarray(offset, dtype=np.float32)
	return values.ravel()
