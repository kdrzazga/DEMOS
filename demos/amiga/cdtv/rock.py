"""The granite ridge the CDTV disc leans on: a few long chamfered slabs, baked into one world-space mesh."""
import math
from dataclasses import dataclass

import numpy as np
from OpenGL.GL import *

from demos.amiga.cdtv import shaders
from demos.amiga.common.gl_util import Mesh, ShaderProgram, rotate_y, rotate_z, translate


@dataclass
class RockSlab:
	center: tuple       # world position
	length: float       # along local x (the ridge direction)
	thickness: float    # local y; generous so the bottom stays below the screen
	depth: float        # local z
	chamfer: float      # bevel cut off the two top edges
	roll: float         # degrees around z: negative = descends to the right
	yaw: float          # degrees around y: positive = left end comes toward the camera


# Eyeballed from CDTVstart.mp4: three parallel ridges stepping toward the viewer at ~45 degrees, peak at
# about (-1.8, 0.05) and reaching the bottom edge left of centre, a low shoulder to the left of the peak
# and one small block at the right foot. Slab centres sit below their top edge by thickness/2 along the roll.
DEFAULT_SLABS = (
	RockSlab(center=(-1.67, -1.42, -0.50), length=2.3, thickness=1.9, depth=0.80, chamfer=0.22, roll=-45, yaw=15),
	RockSlab(center=(-1.52, -1.62, 0.10), length=2.3, thickness=1.9, depth=0.60, chamfer=0.20, roll=-47, yaw=15),
	RockSlab(center=(-1.67, -2.12, 0.70), length=2.0, thickness=1.9, depth=0.55, chamfer=0.18, roll=-50, yaw=15),
	RockSlab(center=(-2.35, -1.00, -0.70), length=1.2, thickness=1.9, depth=0.80, chamfer=0.20, roll=10, yaw=15),
	RockSlab(center=(-0.05, -1.85, 0.00), length=0.8, thickness=1.0, depth=0.80, chamfer=0.16, roll=-30, yaw=10),
)


def slab_triangles(slab):
	"""Flat-shaded triangles (position, normal) of one chamfered prism in world space."""
	half_y, half_z, cut = slab.thickness / 2, slab.depth / 2, slab.chamfer
	section = ((-half_y, -half_z), (-half_y, half_z), (half_y - cut, half_z), (half_y, half_z - cut),
		(half_y, -half_z + cut), (half_y - cut, -half_z))  # (y, z) around the cross-section
	half_x = slab.length / 2
	transform = (translate(*slab.center) @ rotate_z(math.radians(slab.roll)) @ rotate_y(math.radians(slab.yaw)))
	rotation = transform[:3, :3]

	def to_world(x, y, z):
		return (transform @ np.array((x, y, z, 1.0)))[:3]

	triangles = []

	def add_face(corners, local_normal):
		normal = rotation @ np.asarray(local_normal, dtype=np.float32)
		normal /= np.linalg.norm(normal)
		world = [to_world(*corner) for corner in corners]
		for index in range(1, len(world) - 1):
			for point in (world[0], world[index], world[index + 1]):
				triangles.extend((*point, *normal))

	for index, (y0, z0) in enumerate(section):
		y1, z1 = section[(index + 1) % len(section)]
		edge_normal = np.array((0.0, z1 - z0, -(y1 - y0)))
		edge_midpoint = np.array((0.0, (y0 + y1) / 2, (z0 + z1) / 2))
		if np.dot(edge_normal, edge_midpoint) < 0:  # the section is centred on the axis: point away from it
			edge_normal = -edge_normal
		add_face(((-half_x, y0, z0), (half_x, y0, z0), (half_x, y1, z1), (-half_x, y1, z1)), edge_normal)
	for end in (-1, 1):
		add_face([(end * half_x, y, z) for y, z in section], (end, 0.0, 0.0))
	return triangles


class Rock:

	def __init__(self, environment, slabs=DEFAULT_SLABS, grain_scale=60.0):
		self.environment = environment
		self.grain_scale = grain_scale
		vertices = [value for slab in slabs for value in slab_triangles(slab)]
		self.mesh = Mesh(vertices, ((0, 3), (1, 3)), GL_TRIANGLES)
		self.program = ShaderProgram(shaders.ROCK_VERTEX, shaders.ROCK_FRAGMENT)

	def draw(self, scene_time, view_projection, viewport):
		program = self.program
		program.use()
		program.set_float("u_time", scene_time)
		program.set_vec2("u_viewport", *viewport)
		self.environment.apply_uniforms(program, scene_time)
		program.set_mat4("u_view_projection", view_projection)
		program.set_float("u_grain_scale", self.grain_scale)
		glBlendFunc(GL_ONE, GL_ZERO)
		self.mesh.draw()
