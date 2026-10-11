"""Amiga 600 Kickstart 2.0 "insert disk" screen, rebuilt in 3D (pygame-ce + PyOpenGL).

The original screen loops forever, so this does too: a floppy hangs under the drive, dips, tips
back into the slot and slides in; the drive stays empty for a moment and the disk returns
(one cycle = 4.08 s). The drive click (one every 2.52 s) is a seamless audio loop on its own clock.
Esc quits.

Run:  python -m demos.amiga.a600.a600_intro [--fullscreen]
"""
import glob
import math
import os
import sys
from dataclasses import dataclass

import numpy as np
import pygame
from OpenGL.GL import *

from demos.amiga.a600.models import CheckmarkModel, DriveModel, FloppyModel, ref_to_world
from demos.amiga.common import glsl
from demos.amiga.common.extruded_glyphs import ExtrudedGlyphRenderer, GlyphMaterial
from demos.amiga.common.gl_util import clamp01, ease_out_cubic, rotate_x, rotate_y, smoothstep, translate
from demos.amiga.common.glyphs import FONTS_DIR, SpriteFactory
from demos.amiga.common.intro_window import IntroWindow
from demos.amiga.common.meshes import ColoredMeshRenderer

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
BACKGROUND = (0.22, 0.07, 0.22)


class FlatEnvironment:
	"""Nothing to reflect on this screen."""

	def __init__(self):
		self.glsl = "vec4 environment(vec2 uv) { return vec4(0.0); }\n"

	def apply_uniforms(self, program, scene_time):
		pass


@dataclass
class InsertCycle:
	"""Timing of one disk insertion loop, in seconds from the moment the disk reappears.
	Measured frame by frame from a600.mp4 (the first dip happens 2.60 s into the video)."""
	period: float = 4.08
	first_dip_at: float = 2.60
	appear_duration: float = 0.40
	appear_drop: float = 0.12       # the disk rises into place from this far below
	dip_start: float = 1.96
	dip_end: float = 2.12
	dip_depth: float = 0.07
	tilt_end: float = 2.80          # rise to slot height while tipping 90 degrees back
	slide_start: float = 2.74
	slide_end: float = 3.06
	slide_distance: float = 0.88    # how far it travels into the drive

	def cycle_time(self, scene_time):
		since_first_cycle = scene_time - (self.first_dip_at - self.dip_start)
		if since_first_cycle < 0:
			return self.appear_duration   # the video opens with the disk already hanging there
		return since_first_cycle % self.period

	def is_visible(self, cycle_time):
		return cycle_time < self.slide_end


class FloppyInsertion:
	"""Poses the floppy (pivot = its top edge) between its rest spot and the drive slot."""

	def __init__(self, slot_center, cycle=None, rest_top=ref_to_world(349.5, 190.0), rest_z=0.03):
		self.slot_center = slot_center
		self.cycle = cycle or InsertCycle()
		self.rest_top = rest_top
		self.rest_z = rest_z

	def model_matrix(self, scene_time):
		"""None while the disk is inside the drive."""
		cycle = self.cycle
		time_in_cycle = cycle.cycle_time(scene_time)
		if not cycle.is_visible(time_in_cycle):
			return None
		x, y = self.rest_top
		z = self.rest_z
		tilt = 0.0
		if time_in_cycle < cycle.appear_duration:
			y -= cycle.appear_drop * (1.0 - ease_out_cubic(time_in_cycle / cycle.appear_duration))
		elif cycle.dip_start <= time_in_cycle < cycle.dip_end:
			y -= cycle.dip_depth * math.sin(math.pi * (time_in_cycle - cycle.dip_start) / (cycle.dip_end - cycle.dip_start))
		elif time_in_cycle >= cycle.dip_end:
			rise = smoothstep(cycle.dip_end, cycle.tilt_end, time_in_cycle)
			x += (self.slot_center[0] - x) * rise
			y += (self.slot_center[1] - y) * rise
			tilt = -math.pi / 2 * rise
			slide = clamp01((time_in_cycle - cycle.slide_start) / (cycle.slide_end - cycle.slide_start))
			z -= (self.rest_z + cycle.slide_distance) * slide * slide
		return translate(x, y, z) @ rotate_x(tilt)


ROM_LINES = ("2.0 Roms (37.350)", "Copyright © 1985-1991", "Commodore-Amiga, Inc.", "All Rights Reserved")


class RomText:
	"""The four boot-screen lines as thin extruded pixel text in the Amiga Topaz font.
	Looks for a *topaz*.ttf in resources/fonts, then in the Windows fonts folder; Lucida Console
	rendered without antialiasing stands in if neither has one."""

	def __init__(self, environment, lines=ROM_LINES, left=ref_to_world(47.5, 0)[0],
			line_tops=tuple(ref_to_world(0, py)[1] for py in (207.5, 223.0, 238.0, 253.0)),
			char_pitch=0.0624, depth=0.025, font_px=16, pixel_scale=4,
			color=(0.78, 0.58, 0.52), side_color=(0.42, 0.28, 0.25)):
		self.depth = depth
		self.renderer = ExtrudedGlyphRenderer(environment, side_slices=6)
		# the painted material darkens a camera-facing face to ~0.886; compensate so the palette colour survives
		face_color = tuple(min(channel / 0.886, 1.0) for channel in color)
		self.material = GlyphMaterial(glsl.GLYPH_PAINTED, face_color, face_color, side_color)
		font = pygame.font.Font(self._font_path(), font_px)
		world_per_px = char_pitch / (font.size("M")[0] * pixel_scale)
		factory = SpriteFactory(bevel_px=1, pad_px=pixel_scale)
		self.sprites = []
		for line, top in zip(lines, line_tops):
			mask = self._pixel_mask(font, line)
			mask = np.repeat(np.repeat(mask, pixel_scale, axis=0), pixel_scale, axis=1)
			self.sprites.append(factory.make(mask, world_per_px, left, top - mask.shape[0] * world_per_px))

	@staticmethod
	def _pixel_mask(font, line):
		# without antialiasing pygame returns an 8-bit surface with no alpha channel,
		# so render white on black and use the brightness as coverage
		surface = font.render(line, False, (255, 255, 255), (0, 0, 0))
		return pygame.surfarray.array3d(surface)[..., 0].T.astype(np.float32) / 255.0

	@staticmethod
	def _font_path():
		for folder in (os.path.join(RESOURCES_DIR, "fonts"), FONTS_DIR):
			for candidate in sorted(glob.glob(os.path.join(folder, "*[Tt]opaz*.ttf"))):
				return candidate
		for name in ("lucon.ttf", "consola.ttf", "cour.ttf"):
			path = os.path.join(FONTS_DIR, name)
			if os.path.exists(path):
				return path
		return None

	def draw(self, scene_time, view_projection, viewport):
		self.renderer.begin(scene_time, viewport, reflect=0.0)
		for sprite in self.sprites:
			model = translate(sprite.center_x, sprite.center_y, 0.0)
			self.renderer.draw(sprite, model, view_projection, self.material, self.depth)
		self.renderer.end()


class A600Scene:

	def __init__(self, viewport):
		self.meshes = ColoredMeshRenderer()
		self.checkmark = CheckmarkModel().build()
		drive_model = DriveModel()
		self.drive = drive_model.build()
		self.floppy = FloppyModel().build()
		self.insertion = FloppyInsertion(drive_model.slot_center)
		self.text = RomText(FlatEnvironment())

	def draw(self, scene_time, view_projection, viewport):
		glClearColor(*BACKGROUND, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)
		glEnable(GL_DEPTH_TEST)
		identity = np.identity(4, dtype=np.float32)
		self.meshes.begin()
		self.meshes.draw(self.checkmark, identity, view_projection)
		self.meshes.draw(self.drive, identity, view_projection)
		floppy_model = self.insertion.model_matrix(scene_time)
		if floppy_model is not None:
			self.meshes.draw(self.floppy, floppy_model, view_projection)
		self.text.draw(scene_time, view_projection, viewport)


def gentle_sway(yaw_degrees=6.0, yaw_period=14.0, pitch_degrees=3.0, pitch_period=11.0):
	"""Slow camera drift so the screen reads as 3D; the original is perfectly flat."""
	def motion(scene_time):
		yaw = math.radians(yaw_degrees) * math.sin(2 * math.pi * scene_time / yaw_period)
		pitch = math.radians(pitch_degrees) * math.sin(2 * math.pi * scene_time / pitch_period)
		return rotate_y(yaw) @ rotate_x(pitch)
	return motion


def a600_intro(windowed=True):
	window = IntroWindow("Amiga 600", os.path.join(RESOURCES_DIR, "a600_click_loop.wav"), windowed=windowed,
		window_size=(900, 720), camera_motion=gentle_sway(), loop=True)
	window.run(A600Scene)


if __name__ == "__main__":
	a600_intro(windowed="--fullscreen" not in sys.argv)
