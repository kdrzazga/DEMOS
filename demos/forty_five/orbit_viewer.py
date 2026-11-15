import pygame
from OpenGL.GL import *

from demos.forty_five.scene import setup_scene
from lib.pygame_demo import PygameDemo


class OrbitViewer(PygameDemo):

	def __init__(self, title, windowed=False, triggered=False):
		super().__init__(1280, 800, title, fps=60, windowed=windowed, triggered=triggered)

	def configure_orbit(self, yaw, pitch, distance, min_distance, max_distance):
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)
		self.yaw = yaw
		self.pitch = pitch
		self.distance = distance
		self.min_distance = min_distance
		self.max_distance = max_distance
		self.drag_degrees_per_pixel = 0.35
		self.idle_spin_degrees = 0.15
		self.idle_frames_before_spin = 180
		self.frames_since_drag = 0

	def setup(self):
		pygame.mouse.set_visible(True)
		setup_scene(self.width / self.height, self.fov, self.background)
		self.build_model()

	def build_model(self):
		raise NotImplementedError

	def handle_model_event(self, event):
		return

	def update_model(self):
		return

	def draw_model(self):
		raise NotImplementedError

	def handle_event(self, event):
		if event.type == pygame.MOUSEMOTION and event.buttons[0]:
			delta_x, delta_y = event.rel
			self.yaw += delta_x * self.drag_degrees_per_pixel
			self.pitch = max(-89.0, min(89.0, self.pitch + delta_y * self.drag_degrees_per_pixel))
			self.frames_since_drag = 0
		elif event.type == pygame.MOUSEWHEEL:
			self.distance = max(self.min_distance, min(self.max_distance, self.distance * (0.9 ** event.y)))
		else:
			self.handle_model_event(event)

	def step(self):
		self.frames_since_drag += 1
		if self.frames_since_drag > self.idle_frames_before_spin:
			self.yaw += self.idle_spin_degrees
		self.update_model()

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.distance)
		glRotatef(self.pitch, 1.0, 0.0, 0.0)
		glRotatef(self.yaw, 0.0, 1.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		self.draw_model()
