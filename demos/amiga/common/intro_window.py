"""Window, audio and frame loop shared by the Amiga boot intros.

World convention for every intro: perspective camera on +Z looking at the origin, sized so the
z = 0 plane shows `visible_height` world units vertically (3.6 = the 360-line reference videos,
1 world unit = 100 reference pixels).
"""
import math
import time

import pygame
from OpenGL.GL import *

from demos.amiga.common import glsl
from demos.amiga.common.gl_util import ShaderProgram, perspective, smoothstep, translate, unit_quad_mesh


class FadeOverlay:

	def __init__(self):
		self.program = ShaderProgram(glsl.FULLSCREEN_VERTEX, glsl.FADE_FRAGMENT)
		self.quad = unit_quad_mesh()

	def draw(self, darkness):
		if darkness <= 0.0:
			return
		glDisable(GL_DEPTH_TEST)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		self.program.use()
		self.program.set_float("u_darkness", darkness)
		self.quad.draw()


class IntroWindow:
	"""Runs a scene built by `scene_factory(viewport)`; the scene needs draw(scene_time, view_projection, viewport).
	The intro lasts as long as the audio plus `end_hold`."""

	def __init__(self, caption, audio_path, windowed=True, window_size=(960, 720), fov_y=math.radians(30),
			visible_height=3.6, end_hold=0.3, fade_in=(0.0, 0.0), fallback_duration=10.0):
		self.caption = caption
		self.audio_path = audio_path
		self.windowed = windowed
		self.window_size = window_size
		self.fov_y = fov_y
		self.camera_distance = (visible_height / 2) / math.tan(fov_y / 2)
		self.end_hold = end_hold
		self.fade_in = fade_in      # (start, duration) of the fade from black
		self.fallback_duration = fallback_duration

	def _open_window(self):
		pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
		pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 8)
		pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
		flags = pygame.DOUBLEBUF | pygame.OPENGL
		if self.windowed:
			pygame.display.set_mode(self.window_size, flags)
		else:
			pygame.display.set_mode((0, 0), flags | pygame.FULLSCREEN)
		pygame.display.set_caption(self.caption)
		pygame.mouse.set_visible(self.windowed)
		return pygame.display.get_surface().get_size()

	@staticmethod
	def _enable_point_sprites():
		# pygame gives a compatibility context, where gl_PointCoord stays (0,0) unless point sprites are on
		try:
			glEnable(GL_POINT_SPRITE)
		except GLError:
			pass  # core profile: always enabled, and the enum is invalid

	def _audio_length(self):
		try:
			return pygame.mixer.Sound(self.audio_path).get_length()
		except (pygame.error, FileNotFoundError):
			return self.fallback_duration

	def _darkness(self, scene_time):
		start, duration = self.fade_in
		if duration <= 0:
			return 0.0
		return 1.0 - smoothstep(start, start + duration, scene_time)

	def run(self, scene_factory):
		pygame.mixer.pre_init(44100, -16, 2, 1024)
		pygame.init()
		viewport = self._open_window()
		glViewport(0, 0, *viewport)
		glEnable(GL_MULTISAMPLE)
		glEnable(GL_PROGRAM_POINT_SIZE)
		self._enable_point_sprites()
		glEnable(GL_BLEND)

		scene = scene_factory(viewport)
		fade = FadeOverlay()
		projection = perspective(self.fov_y, viewport[0] / viewport[1], 0.1, 100.0)
		view_projection = projection @ translate(0.0, 0.0, -self.camera_distance)
		duration = self._audio_length() + self.end_hold

		pygame.mixer.music.load(self.audio_path)
		pygame.mixer.music.play()
		started = time.perf_counter()
		clock = pygame.time.Clock()
		running = True
		while running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
					running = False
			scene_time = time.perf_counter() - started
			if scene_time > duration:
				break

			glClearColor(0.0, 0.0, 0.0, 1.0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			scene.draw(scene_time, view_projection, viewport)
			fade.draw(self._darkness(scene_time))
			pygame.display.flip()
			clock.tick(120)

		pygame.mixer.music.stop()
		pygame.quit()
