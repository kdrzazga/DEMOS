from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.graffitti.kna2.komoda_amiga_plus_graffiti import KomodaAmigaPlusGraffiti
from lib.graffitti.swaying_surface import SwayingSurface


class KomodaAmigaPlusAnimation:

	def __init__(self, window_size):
		self.window_size = window_size
		self.field_of_view_degrees = 45.0
		self.camera_distance = 7.2
		self.surface_height = 4.4
		self.hold_seconds = 4.0
		self.wave_stagger_seconds = 0.08
		self.wall_color = (0.62, 0.6, 0.56)
		self.graffiti = KomodaAmigaPlusGraffiti()
		self.surface = SwayingSurface(self.surface_height * self.graffiti.aspect_ratio, self.surface_height)
		self.elapsed_seconds = 0.0
		self.sway_seconds = 0.0
		self.paused = False
		self.showing_finished = False

	def restart(self):
		self.showing_finished = False
		self._rewind()

	def toggle_pause(self):
		self.paused = not self.paused

	def show_finished(self):
		self.showing_finished = True
		self.elapsed_seconds = max(self.elapsed_seconds, self.graffiti.drawn_seconds)

	def blink(self):
		self.graffiti.blink_all_outlines(self.elapsed_seconds)

	def blink_wave(self):
		self.graffiti.blink_all_outlines(self.elapsed_seconds, self.wave_stagger_seconds)

	def update(self, frame_seconds):
		if self.paused:
			return
		self.elapsed_seconds += frame_seconds
		self.sway_seconds += frame_seconds
		if not self.showing_finished and self.elapsed_seconds > self.graffiti.duration_seconds + self.hold_seconds:
			self._rewind()

	def render(self):
		self.graffiti.render(self.elapsed_seconds)
		self.surface.update(self.sway_seconds)
		self._set_camera()
		glClearColor(*self.wall_color, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.surface.render(self.graffiti.texture)

	def _rewind(self):
		self.elapsed_seconds = 0.0
		self.graffiti.reset_outline_blinks()

	def _set_camera(self):
		glViewport(0, 0, *self.window_size)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(self.field_of_view_degrees, self.window_size[0] / self.window_size[1], 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.camera_distance)
