"""Draws GlyphSprites as solid 3D letters: stacked extrusion slices behind a bevel-lit front face."""
from dataclasses import dataclass

from OpenGL.GL import *

from demos.amiga.common import glsl
from demos.amiga.common.gl_util import ShaderProgram, unit_quad_mesh


@dataclass
class GlyphMaterial:
	kind: int                       # glsl.GLYPH_PAINTED / GLYPH_CHROME / GLYPH_SKY_CHROME
	color_low: tuple
	color_high: tuple
	side_color: tuple


class ExtrudedGlyphRenderer:

	def __init__(self, environment, side_slices=22):
		self.environment = environment
		self.side_slices = side_slices
		self.program = ShaderProgram(glsl.GLYPH_VERTEX, glsl.glyph_fragment(environment.glsl))
		self.quad = unit_quad_mesh()

	def begin(self, scene_time, viewport, reflect):
		program = self.program
		program.use()
		program.set_float("u_time", scene_time)
		program.set_vec2("u_viewport", *viewport)
		self.environment.apply_uniforms(program, scene_time)
		program.set_int("u_glyph", 0)
		program.set_float("u_reflect", reflect)
		glActiveTexture(GL_TEXTURE0)
		glEnable(GL_SAMPLE_ALPHA_TO_COVERAGE)
		glBlendFunc(GL_ONE, GL_ZERO)

	def end(self):
		glDisable(GL_SAMPLE_ALPHA_TO_COVERAGE)

	def draw(self, sprite, model, view_projection, material, depth, alpha=1.0):
		"""`model` places the glyph centre; it must be rotation + translation only (no scale)."""
		program = self.program
		program.set_mat4("u_mvp", view_projection @ model)
		program.set_mat3("u_normal_matrix", model[:3, :3])
		program.set_vec2("u_size", sprite.width, sprite.height)
		program.set_float("u_slant", sprite.slant)
		program.set_int("u_material", material.kind)
		program.set_vec3("u_color_low", *material.color_low)
		program.set_vec3("u_color_high", *material.color_high)
		program.set_vec3("u_side_color", *material.side_color)
		program.set_float("u_alpha", alpha)
		glBindTexture(GL_TEXTURE_2D, sprite.texture)
		slices = self.side_slices if depth > 0 else 0
		program.set_int("u_is_side", 1)
		for layer in range(slices, 0, -1):
			fraction = layer / slices
			program.set_float("u_layer_z", -depth * fraction)
			program.set_float("u_layer_fraction", fraction)
			self.quad.draw()
		program.set_int("u_is_side", 0)
		program.set_float("u_layer_z", 0.0)
		self.quad.draw()
