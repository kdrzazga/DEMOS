"""Compact disc: a flat iridescent face plus a thin cylindrical edge, posed by the scene."""
import math
from dataclasses import dataclass

import numpy as np
from OpenGL.GL import *

from demos.amiga.common import glsl
from demos.amiga.common.gl_util import Mesh, ShaderProgram, scale, unit_quad_mesh


@dataclass
class DiscLook:
	base_dark: tuple = (0.66, 0.65, 0.73)
	base_light: tuple = (0.97, 0.90, 0.86)
	sheen_direction: tuple = (0.45, 0.8)    # disc-local direction from dark to light
	spoke_strength: float = 1.0
	light_angle: float = 0.85               # angle of the strongest rainbow fan, disc-local radians
	light_wobble: float = 0.12
	reflect: float = 0.55
	environment_offset: tuple = (0.0, 0.32) # where on screen the reflection is sampled, relative to the fragment
	hole_radius: float = 0.125
	thickness: float = 0.035                # world units


def cylinder_mesh(segments):
	vertices = []
	for index in range(segments):
		a0 = 2 * math.pi * index / segments
		a1 = 2 * math.pi * (index + 1) / segments
		p0 = (math.cos(a0), math.sin(a0))
		p1 = (math.cos(a1), math.sin(a1))
		for x, y, depth in ((*p0, 0), (*p1, 0), (*p1, 1), (*p0, 0), (*p1, 1), (*p0, 1)):
			vertices += (x, y, depth)
	return Mesh(vertices, ((0, 3),), GL_TRIANGLES)


class Disc:
	"""`pose(scene_time)` returns the model matrix of a unit disc lying in its local XY plane (face = +Z).
	While scene_time < motion_blur_until, ghost copies at earlier times are drawn behind it."""

	def __init__(self, environment, pose, radius, look=None, visible_from=0.0, motion_blur_until=0.0,
			ghost_count=5, ghost_spacing=0.025):
		self.environment = environment
		self.pose = pose
		self.radius = radius
		self.look = look or DiscLook()
		self.visible_from = visible_from
		self.motion_blur_until = motion_blur_until
		self.ghost_count = ghost_count
		self.ghost_spacing = ghost_spacing
		self.program = ShaderProgram(glsl.DISC_VERTEX, glsl.disc_fragment(environment.glsl))
		self.edge_program = ShaderProgram(glsl.DISC_EDGE_VERTEX, glsl.DISC_EDGE_FRAGMENT)
		self.quad = unit_quad_mesh()
		self.edge = cylinder_mesh(96)

	def model_matrix(self, sample_time):
		return self.pose(sample_time) @ scale(self.radius, self.radius, self.radius)

	def _draw_once(self, sample_time, scene_time, view_projection, viewport, alpha):
		look = self.look
		mvp = view_projection @ self.model_matrix(sample_time)
		self.edge_program.use()
		self.edge_program.set_mat4("u_mvp", mvp)
		self.edge_program.set_float("u_thickness", look.thickness / self.radius)
		self.edge_program.set_float("u_alpha", alpha)
		self.edge.draw()

		program = self.program
		program.use()
		program.set_float("u_time", scene_time)
		program.set_vec2("u_viewport", *viewport)
		self.environment.apply_uniforms(program, scene_time)
		program.set_mat4("u_mvp", mvp)
		wobble = math.sin(scene_time * 0.9) + 0.4 * math.sin(scene_time * 2.3)
		program.set_float("u_light_angle", look.light_angle + look.light_wobble * wobble)
		program.set_float("u_spoke_strength", look.spoke_strength)
		program.set_vec3("u_base_dark", *look.base_dark)
		program.set_vec3("u_base_light", *look.base_light)
		sheen = np.asarray(look.sheen_direction, dtype=np.float32)
		program.set_vec2("u_sheen_direction", *(sheen / np.linalg.norm(sheen)))
		program.set_float("u_reflect", look.reflect)
		program.set_vec2("u_environment_offset", *look.environment_offset)
		program.set_float("u_alpha", alpha)
		program.set_float("u_hole_radius", look.hole_radius)
		self.quad.draw()

	def draw(self, scene_time, view_projection, viewport):
		if scene_time < self.visible_from:
			return
		if scene_time < self.motion_blur_until:
			glDisable(GL_SAMPLE_ALPHA_TO_COVERAGE)
			glDepthMask(GL_FALSE)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			for ghost in range(self.ghost_count, 0, -1):
				sample_time = scene_time - ghost * self.ghost_spacing
				if sample_time >= self.visible_from:
					self._draw_once(sample_time, scene_time, view_projection, viewport, 0.45 / ghost)
			glDepthMask(GL_TRUE)
		glEnable(GL_SAMPLE_ALPHA_TO_COVERAGE)
		glBlendFunc(GL_ONE, GL_ZERO)
		self._draw_once(scene_time, scene_time, view_projection, viewport, 1.0)
		glDisable(GL_SAMPLE_ALPHA_TO_COVERAGE)
