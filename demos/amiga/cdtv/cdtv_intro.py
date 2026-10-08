"""Commodore CDTV boot animation, rebuilt in 3D (pygame-ce + PyOpenGL).

A disc leans on a granite ridge under a violet-to-pink sky, a light beam runs from it to the
right edge, and a chrome "CDTV" written around a spinning cylinder turns above.

Run:  python -m demos.amiga.cdtv.cdtv_intro [--fullscreen]
"""
import math
import os
import sys

import numpy as np
from OpenGL.GL import *

from demos.amiga.cdtv import shaders
from demos.amiga.cdtv.rock import Rock
from demos.amiga.common import glsl
from demos.amiga.common.disc import Disc, DiscLook
from demos.amiga.common.extruded_glyphs import ExtrudedGlyphRenderer, GlyphMaterial
from demos.amiga.common.gl_util import ShaderProgram, rotate_y, rotate_z, translate, unit_quad_mesh
from demos.amiga.common.glyphs import RoundedGlyphPainter, SpriteFactory
from demos.amiga.common.intro_window import IntroWindow

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")


class Sky:
	"""Vertical gradient background; also the reflection environment for the disc, title and rock."""

	def __init__(self, top=(0.42, 0.42, 0.94), middle=(0.62, 0.45, 0.86), bottom=(0.88, 0.44, 0.55)):
		self.glsl = shaders.SKY_GLSL
		self.top = top
		self.middle = middle
		self.bottom = bottom
		self.program = ShaderProgram(glsl.FULLSCREEN_VERTEX, shaders.SKY_FRAGMENT)
		self.quad = unit_quad_mesh()

	def apply_uniforms(self, program, scene_time):
		program.set_vec3("u_sky_top", *self.top)
		program.set_vec3("u_sky_middle", *self.middle)
		program.set_vec3("u_sky_bottom", *self.bottom)

	def draw(self, scene_time, viewport):
		self.program.use()
		self.program.set_float("u_time", scene_time)
		self.program.set_vec2("u_viewport", *viewport)
		self.apply_uniforms(self.program, scene_time)
		glBlendFunc(GL_ONE, GL_ZERO)
		self.quad.draw()


PIXELS_PER_CM_AT_720P = 37.8   # 96 dpi


class LightBeam:
	"""Laser line that hits the disc face and disperses there, running to the right screen edge.

	The hit point starts at `disc_point` (disc-local, radius 1; local -y points down-right on the leaning
	disc), is nudged on screen by `screen_offset_cm` (x < 0 = deeper into the disc, y > 0 = higher),
	then cast back onto the disc plane and kept on the reflective area between `surface_radii`."""

	def __init__(self, disc, disc_point=(0.40, -0.13), screen_offset_cm=(0.0, 0.0), surface_radii=(0.38, 0.95),
			strength=1.0):
		self.disc = disc
		self.disc_point = disc_point
		self.screen_offset_cm = screen_offset_cm
		self.surface_radii = surface_radii
		self.strength = strength
		self.program = ShaderProgram(glsl.FULLSCREEN_VERTEX, shaders.BEAM_FRAGMENT)
		self.quad = unit_quad_mesh()

	@staticmethod
	def _project(view_projection, world_point):
		clip = view_projection @ np.append(world_point, 1.0)
		return clip[:2] / clip[3]

	def _clamp_to_surface(self, local_xy):
		radius = np.linalg.norm(local_xy)
		inner, outer = self.surface_radii
		if radius < 1e-6:
			return np.array((0.0, -inner))
		return local_xy * (min(max(radius, inner), outer) / radius)

	def hit_point_ndc(self, scene_time, view_projection, viewport):
		model = self.disc.model_matrix(scene_time)
		start = (model @ np.array((*self.disc_point, 0.0, 1.0)))[:3]
		pixels_per_cm = PIXELS_PER_CM_AT_720P * viewport[1] / 720.0
		target_ndc = self._project(view_projection, start) + np.array(
			[2.0 * cm * pixels_per_cm / size for cm, size in zip(self.screen_offset_cm, viewport)])

		# camera ray through the nudged screen point, intersected with the disc plane
		inverse = np.linalg.inv(view_projection)
		near, far = (inverse @ np.array((*target_ndc, depth, 1.0)) for depth in (-1.0, 1.0))
		near, far = near[:3] / near[3], far[:3] / far[3]
		disc_center = model[:3, 3]
		disc_normal = model[:3, :3] @ np.array((0.0, 0.0, 1.0))
		direction = far - near
		along = np.dot(disc_center - near, disc_normal) / np.dot(direction, disc_normal)
		hit_world = near + direction * along

		local = (np.linalg.inv(model) @ np.append(hit_world, 1.0))[:2]
		surface_local = self._clamp_to_surface(local)
		return self._project(view_projection, (model @ np.array((*surface_local, 0.0, 1.0)))[:3])

	def draw(self, scene_time, view_projection, viewport):
		self.program.use()
		self.program.set_float("u_time", scene_time)
		self.program.set_vec2("u_viewport", *viewport)
		self.program.set_vec2("u_beam_origin", *(self.hit_point_ndc(scene_time, view_projection, viewport) * 0.5 + 0.5))
		self.program.set_float("u_strength", self.strength)
		glBlendFunc(GL_ONE, GL_ONE)
		self.quad.draw()


SKY_CHROME = GlyphMaterial(glsl.GLYPH_SKY_CHROME, color_low=(0.45, 0.45, 0.95), color_high=(0.97, 0.97, 1.0),
	side_color=(0.92, 0.93, 1.0))


class TitleRing:
	"""`copies` x the word written around a vertical cylinder whose front moves to the left.
	Condensed rounded-square letters, extruded inward toward the cylinder axis."""

	def __init__(self, environment, word="CDTV", copies=3, center=(0.82, 0.54), letter_height=0.55,
			letter_gap=0.05, word_gap=0.38, depth=0.14, seconds_per_turn=4.8, material=SKY_CHROME, render_px=200):
		self.center = center
		self.depth = depth
		self.seconds_per_turn = seconds_per_turn
		self.material = material
		self.renderer = ExtrudedGlyphRenderer(environment)
		painter = RoundedGlyphPainter(render_px, width_ratio=0.74, stroke_ratio=0.25, outer_radius_ratio=0.24)
		factory = SpriteFactory(bevel_px=4)
		sprites = {}
		ink_widths = {}
		for character in set(word):
			mask = painter.glyph(character)
			sprites[character] = factory.make_by_height(mask, letter_height)
			ink_widths[character] = mask.shape[1] * letter_height / mask.shape[0]
		# lay the letters out along the circumference by arc length
		self.letters = []   # (sprite, arc position of the letter centre)
		arc = 0.0
		for _ in range(copies):
			for index, character in enumerate(word):
				if index:
					arc += letter_gap
				self.letters.append((sprites[character], arc + ink_widths[character] / 2))
				arc += ink_widths[character]
			arc += word_gap
		self.radius = arc / (2 * math.pi)

	def draw(self, scene_time, view_projection, viewport):
		turn = -2 * math.pi * scene_time / self.seconds_per_turn
		axis = translate(self.center[0], self.center[1], -self.radius)
		self.renderer.begin(scene_time, viewport, reflect=1.0)
		for sprite, arc_position in self.letters:
			angle = turn + arc_position / self.radius
			if math.cos(angle) < -0.2:
				continue  # on the far side of the cylinder
			model = axis @ rotate_y(angle) @ translate(0.0, 0.0, self.radius)
			self.renderer.draw(sprite, model, view_projection, self.material, self.depth)
		self.renderer.end()


def leaning_disc_pose(position=(-1.15, -0.45, 0.5), lean=math.radians(35), turn=math.radians(71)):
	"""Disc standing on its edge: face turned toward the right, top leaning to the left."""
	pose = translate(*position) @ rotate_z(lean) @ rotate_y(turn)
	return lambda scene_time: pose


CDTV_DISC_LOOK = DiscLook(base_dark=(0.55, 0.60, 0.90), base_light=(0.92, 0.95, 1.0), sheen_direction=(-0.3, 1.0),
	spoke_strength=0.45, light_angle=2.4, light_wobble=0.04, reflect=0.55, environment_offset=(0.08, 0.15))


class CdtvScene:

	def __init__(self, viewport):
		self.sky = Sky()
		self.rock = Rock(self.sky)
		self.disc = Disc(self.sky, leaning_disc_pose(), radius=0.85, look=CDTV_DISC_LOOK)
		self.title = TitleRing(self.sky)
		self.beam = LightBeam(self.disc)

	def draw(self, scene_time, view_projection, viewport):
		glDisable(GL_DEPTH_TEST)
		self.sky.draw(scene_time, viewport)
		glEnable(GL_DEPTH_TEST)
		self.rock.draw(scene_time, view_projection, viewport)
		self.disc.draw(scene_time, view_projection, viewport)
		self.title.draw(scene_time, view_projection, viewport)
		glDisable(GL_DEPTH_TEST)
		self.beam.draw(scene_time, view_projection, viewport)


def cdtv_intro(windowed=True):
	window = IntroWindow("Commodore CDTV", os.path.join(RESOURCES_DIR, "CDTVstart.wav"), windowed=windowed,
		fade_in=(0.15, 0.35), fallback_duration=5.2)
	window.run(CdtvScene)


if __name__ == "__main__":
	cdtv_intro(windowed="--fullscreen" not in sys.argv)
