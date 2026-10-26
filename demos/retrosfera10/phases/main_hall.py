import math

import pygame
from OpenGL.GL import (
	GL_BLEND, GL_CLAMP_TO_EDGE, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_LIGHTING, GL_LINEAR,
	GL_MODELVIEW, GL_ONE_MINUS_SRC_ALPHA, GL_PROJECTION, GL_QUADS, GL_RGBA, GL_SRC_ALPHA, GL_TEXTURE_2D,
	GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_UNSIGNED_BYTE, glBegin,
	glBindTexture, glBlendFunc, glClear, glClearColor, glColor4f, glDisable, glEnable, glEnd, glGenTextures,
	glLoadIdentity, glMatrixMode, glPopMatrix, glPushMatrix, glTexCoord2f, glTexImage2D, glTexParameteri, glVertex2f,
)
from OpenGL.GLU import gluOrtho2D

from lib.demo_phases import CameraInterpolationHelper, Light, DemoPhase
from demos.retrosfera10.models.mainhall import MainHall
from demos.retrosfera10.models.townhall import Vector3


class MainHallTimeline:
	def __init__(self, walk=18.0, screen_delay=3.0, screen_appear=1.5, caption_hold=5.0, dolls_delay=3.0,
			logo_zoom_delay=math.inf, logo_zoom=0.5, logo_only=1.5):
		"""logo_zoom_delay inf keeps the camera in the hall for good; a finite one ends on the logo alone."""
		self.walk = walk
		self.dolls_delay = dolls_delay
		self.screen_delay = screen_delay
		self.screen_appear = screen_appear
		self.caption_hold = caption_hold
		self.logo_zoom_delay = logo_zoom_delay
		self.logo_zoom = logo_zoom
		self.logo_only = logo_only

	def logo_time(self):
		return self.screen_delay + self.screen_appear + self.caption_hold

	def logo_only_time(self):
		return self.logo_zoom_delay + self.logo_zoom

	def end_time(self):
		return self.logo_only_time() + self.logo_only


class TimedEvent:
	def __init__(self, time, action):
		self.time = time
		self.action = action
		self.fired = False

	def fire_if_due(self, elapsed):
		if not self.fired and elapsed >= self.time:
			self.fired = True
			self.action()


class LogoCard:
	def __init__(self, image_path):
		surface = pygame.image.load(image_path)
		self.width, self.height = surface.get_size()
		pixels = pygame.image.tobytes(surface, "RGBA", True)
		self.texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)

	def draw_across(self, screen_width, screen_height):
		card_height = screen_width * self.height / self.width
		bottom = (screen_height - card_height) / 2
		top = bottom + card_height
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		gluOrtho2D(0, screen_width, 0, screen_height)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_LIGHTING)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0)
		glVertex2f(0.0, bottom)
		glTexCoord2f(1.0, 0.0)
		glVertex2f(screen_width, bottom)
		glTexCoord2f(1.0, 1.0)
		glVertex2f(screen_width, top)
		glTexCoord2f(0.0, 1.0)
		glVertex2f(0.0, top)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_BLEND)
		glEnable(GL_LIGHTING)
		glEnable(GL_DEPTH_TEST)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)


class MainHallDemoPhase(DemoPhase):
	def __init__(self, camera, timeline=None, hall=None):
		super().__init__(camera)
		self.timeline = timeline or MainHallTimeline()
		self.background_color = (0.0, 0.0, 0.0)
		self.light = Light(Vector3(0.3, 1.0, 0.45), (0.56, 0.54, 0.5, 1.0), (0.5, 0.48, 0.44, 1.0))
		self.hall = hall or MainHall()
		self.logo_card = LogoCard(self.hall.logo_path())
		far_wall = -self.hall.half_length
		self.start_eye = Vector3(0.0, 2.6, self.hall.half_length - 0.5)
		stage_center_x = (self.hall.stage.left_x + self.hall.stage.right_x) / 2
		self.end_eye = Vector3(stage_center_x, 1.9, self.hall.stage_front() + 9.0)
		self.start_target = Vector3(0.0, 2.6, far_wall)
		self.end_target = Vector3(stage_center_x, 1.6, far_wall)
		self.events = (
			TimedEvent(self.timeline.dolls_delay, self.hall.start_dolls_jumping),
			TimedEvent(self.timeline.logo_time(), self.hall.show_screen_logo),
		)

	def update(self, seconds):
		super().update(seconds)
		self.hall.update(seconds)
		for event in self.events:
			event.fire_if_due(self.elapsed)
		self.done = self.elapsed >= self.timeline.end_time()

	def logo_filling_view(self):
		"""Eye and target from which the screen logo spans the view from the left edge to the right edge."""
		center, width = self.hall.logo_area()
		half_view = math.tan(math.radians(self.camera.field_of_view) / 2) * self.camera.screen_width / self.camera.screen_height
		distance = width / 2 / half_view
		return Vector3(center.x, center.y, center.z + distance), center

	def render(self):
		glClearColor(*self.background_color, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		if self.elapsed >= self.timeline.logo_only_time():
			self.logo_card.draw_across(self.camera.screen_width, self.camera.screen_height)
			return
		self.camera.apply_projection(0.1, 200.0)
		walk = CameraInterpolationHelper.smooth(self.elapsed / self.timeline.walk)
		eye = CameraInterpolationHelper.blend(self.start_eye, self.end_eye, walk)
		target = CameraInterpolationHelper.blend(self.start_target, self.end_target, walk)
		zoom = CameraInterpolationHelper.smooth((self.elapsed - self.timeline.logo_zoom_delay) / self.timeline.logo_zoom)
		if zoom > 0.0:
			logo_eye, logo_target = self.logo_filling_view()
			eye = CameraInterpolationHelper.blend(eye, logo_eye, zoom)
			target = CameraInterpolationHelper.blend(target, logo_target, zoom)
		self.camera.look(eye, target, Vector3.up())
		self.light.apply()
		screen_visibility = CameraInterpolationHelper.smooth((self.elapsed - self.timeline.screen_delay) / self.timeline.screen_appear)
		self.hall.draw(screen_visibility)
