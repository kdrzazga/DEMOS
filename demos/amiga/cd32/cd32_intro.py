"""Amiga CD32 boot animation, rebuilt in 3D (pygame-ce + PyOpenGL).

Run:  python -m demos.amiga.cd32.cd32_intro [--fullscreen]
"""
import math
import os
import random
import sys
from dataclasses import dataclass

from OpenGL.GL import *

from demos.amiga.cd32 import shaders
from demos.amiga.cd32.logo_glyphs import Cd32LogoGlyphBuilder
from demos.amiga.common import glsl
from demos.amiga.common.disc import Disc, DiscLook
from demos.amiga.common.extruded_glyphs import ExtrudedGlyphRenderer, GlyphMaterial
from demos.amiga.common.gl_util import (Mesh, ShaderProgram, clamp01, ease_out_cubic, rotate_x, rotate_y, rotate_z,
	smoothstep, translate, unit_quad_mesh)
from demos.amiga.common.intro_window import IntroWindow

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")


@dataclass
class WavePulse:
	start: float
	travel: float          # seconds for the front to cross the whole band
	color_duration: float  # seconds each point spends cycling through its hues
	band: int              # 0 = sky (rises from under the logo), 1 = ground (sinks from under the disc)
	hue_front: float = 0.78
	hue_tail: float = 0.0
	saturation: float = 0.85
	brightness: float = 1.0


# Timings read off cd32start.mp4 frame by frame.
DEFAULT_PULSES = (
	WavePulse(2.40, 0.80, 1.80, band=0),
	WavePulse(3.90, 0.70, 1.60, band=1, hue_tail=0.02),
	WavePulse(6.95, 0.55, 0.75, band=0, hue_front=0.80, hue_tail=0.70),
	WavePulse(7.85, 0.65, 3.40, band=1, hue_front=0.92, hue_tail=0.0, saturation=0.75, brightness=0.8),
	WavePulse(9.85, 0.55, 1.80, band=0, hue_tail=-0.02),
	WavePulse(13.40, 0.70, 2.50, band=1, hue_front=0.80),
	WavePulse(13.90, 0.60, 2.00, band=0, hue_front=0.90, hue_tail=0.60),
)


class Aurora:
	"""The rainbow waves; also the reflection environment for the disc and logo."""

	def __init__(self, pulses=DEFAULT_PULSES, sky_horizon=0.62, ground_horizon=0.38):
		self.glsl = shaders.AURORA_GLSL
		self.pulses = pulses
		self.sky_horizon = sky_horizon
		self.ground_horizon = ground_horizon
		self.program = ShaderProgram(glsl.FULLSCREEN_VERTEX, shaders.AURORA_FRAGMENT)
		self.quad = unit_quad_mesh()

	def apply_uniforms(self, program, scene_time):
		program.set_int("u_pulse_count", len(self.pulses))
		program.set_vec4_array("u_pulse_timing", [(p.start, p.travel, p.color_duration, p.band) for p in self.pulses])
		program.set_vec4_array("u_pulse_look", [(p.hue_front, p.hue_tail, p.saturation, p.brightness) for p in self.pulses])
		program.set_float("u_sky_horizon", self.sky_horizon)
		program.set_float("u_ground_horizon", self.ground_horizon)

	def draw(self, scene_time, viewport):
		self.program.use()
		self.program.set_float("u_time", scene_time)
		self.program.set_vec2("u_viewport", *viewport)
		self.apply_uniforms(self.program, scene_time)
		glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		self.quad.draw()


class Starfield:

	def __init__(self, dot_count=420, sparkle_count=46, seed=32, appear_at=0.85, appear_duration=0.15):
		self.appear_at = appear_at
		self.appear_duration = appear_duration
		rng = random.Random(seed)
		vertices = []
		for index in range(dot_count + sparkle_count):
			is_sparkle = index >= dot_count
			size = rng.uniform(7.0, 11.0) if is_sparkle else rng.uniform(1.5, 3.0)
			vertices += (rng.uniform(-1, 1), rng.uniform(-1, 1), size, float(is_sparkle), rng.random())
		self.mesh = Mesh(vertices, ((0, 2), (1, 1), (2, 1), (3, 1)), GL_POINTS)
		self.program = ShaderProgram(shaders.STARS_VERTEX, shaders.STARS_FRAGMENT)

	def draw(self, scene_time, viewport):
		fade = clamp01((scene_time - self.appear_at) / self.appear_duration)
		if fade <= 0:
			return
		self.program.use()
		self.program.set_float("u_time", scene_time)
		self.program.set_float("u_pixel_scale", viewport[1] / 720.0)
		self.program.set_float("u_fade", fade)
		glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		self.mesh.draw()


class DiscFlight:
	"""Pose of the disc: tumbles in from the far top-right, then rests under the logo."""

	def __init__(self, start=0.95, duration=0.65, start_position=(2.6, 2.6, -11.0), rest_position=(0.0, -0.2, 0.0),
			rest_tilt=math.radians(-75)):
		self.start = start
		self.duration = duration
		self.start_position = start_position
		self.rest_position = rest_position
		self.rest_tilt = rest_tilt

	@property
	def end(self):
		return self.start + self.duration

	def __call__(self, scene_time):
		eased = ease_out_cubic((scene_time - self.start) / self.duration)
		position = [s + (r - s) * eased for s, r in zip(self.start_position, self.rest_position)]
		remaining = 1.0 - eased
		tilt = self.rest_tilt + math.radians(45) * remaining
		return translate(*position) @ rotate_z(-0.8 * remaining) @ rotate_y(0.9 * remaining) @ rotate_x(tilt)


@dataclass
class SpinIn:
	"""A glyph that arrives at `start`, spins around its vertical axis and settles at `start + duration`."""
	start: float
	duration: float
	turns: float
	slide_from_x: float = 0.0     # extra x offset at the start, eased out over slide_duration
	slide_duration: float = 0.0
	fade_duration: float = 0.12

	def state(self, scene_time):
		progress = clamp01((scene_time - self.start) / self.duration)
		spin = self.turns * 2 * math.pi * (1.0 - progress) ** 2
		slide_progress = clamp01((scene_time - self.start) / self.slide_duration) if self.slide_duration else 1.0
		x_offset = self.slide_from_x * (1.0 - ease_out_cubic(slide_progress))
		alpha = clamp01((scene_time - self.start) / self.fade_duration) if self.fade_duration else 1.0
		return spin, x_offset, alpha


@dataclass
class LogoPiece:
	sprite: object
	material: GlyphMaterial
	depth: float
	motion: SpinIn


RED_PAINT = GlyphMaterial(glsl.GLYPH_PAINTED, color_low=(0.78, 0.17, 0.06), color_high=(1.0, 0.45, 0.20),
	side_color=(0.50, 0.10, 0.04))
SILVER = GlyphMaterial(glsl.GLYPH_CHROME, color_low=(0.60, 0.60, 0.66), color_high=(0.97, 0.97, 0.99),
	side_color=(0.62, 0.62, 0.68))


class Logo:

	def __init__(self, aurora, builder=None, reflect_until=4.2, reflect_settle=0.6, reflect_rest=0.12):
		self.reflect_until = reflect_until
		self.reflect_settle = reflect_settle
		self.reflect_rest = reflect_rest
		self.renderer = ExtrudedGlyphRenderer(aurora)
		builder = builder or Cd32LogoGlyphBuilder()
		self.pieces = []
		for index, sprite in enumerate(builder.build_amiga_letters()):
			self.pieces.append(LogoPiece(sprite, RED_PAINT, 0.10, SpinIn(2.70 + 0.06 * index, 0.60, turns=1.5)))
		self.pieces.append(LogoPiece(builder.build_cd(), SILVER, 0.16,
			SpinIn(2.35, 1.65, turns=2.0, slide_from_x=-4.2, slide_duration=0.65, fade_duration=0.0)))
		self.pieces.append(LogoPiece(builder.build_32(), RED_PAINT, 0.08, SpinIn(2.95, 0.45, turns=1.0)))
		self.pieces.append(LogoPiece(builder.build_trademark(), RED_PAINT, 0.0, SpinIn(4.35, 0.25, turns=0.0, fade_duration=0.25)))

	def reflectivity(self, scene_time):
		settle = smoothstep(self.reflect_until, self.reflect_until + self.reflect_settle, scene_time)
		return 0.9 + (self.reflect_rest - 0.9) * settle

	def draw(self, scene_time, view_projection, viewport):
		self.renderer.begin(scene_time, viewport, self.reflectivity(scene_time))
		for piece in self.pieces:
			if scene_time < piece.motion.start:
				continue
			spin, x_offset, alpha = piece.motion.state(scene_time)
			sprite = piece.sprite
			model = translate(sprite.center_x + x_offset, sprite.center_y, 0.0) @ rotate_y(spin)
			self.renderer.draw(sprite, model, view_projection, piece.material, piece.depth, alpha)
		self.renderer.end()


class Cd32Scene:

	def __init__(self, viewport):
		self.aurora = Aurora()
		self.stars = Starfield()
		flight = DiscFlight()
		self.disc = Disc(self.aurora, flight, radius=1.6, look=DiscLook(), visible_from=flight.start,
			motion_blur_until=flight.end)
		self.logo = Logo(self.aurora)

	def draw(self, scene_time, view_projection, viewport):
		glDisable(GL_DEPTH_TEST)
		self.stars.draw(scene_time, viewport)
		self.aurora.draw(scene_time, viewport)
		glEnable(GL_DEPTH_TEST)
		self.disc.draw(scene_time, view_projection, viewport)
		self.logo.draw(scene_time, view_projection, viewport)


def cd32_intro(windowed=True):
	window = IntroWindow("Amiga CD32", os.path.join(RESOURCES_DIR, "cd32start.wav"), windowed=windowed,
		fallback_duration=14.7)
	window.run(Cd32Scene)


if __name__ == "__main__":
	cd32_intro(windowed="--fullscreen" not in sys.argv)
