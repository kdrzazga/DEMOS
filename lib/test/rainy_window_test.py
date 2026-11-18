import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.rainy_window import RainyWindow


class RainyWindowTest:

	def __init__(self):
		self.window_size = (1280, 720)
		self.frames_per_second = 60
		self.longest_frame_seconds = 0.1
		self.rainfall_step = 1.25
		self.blue_shade_step = 0.1
		self.picture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "NRG26.jpg")
		self.caption = ("Rainy Window - {:.0f} droplets/s, {} running, blue shade {:.1f}  "
		                "(UP/DOWN rainfall, U/D blue shade, X dry the pane, SPACE pause, ESC quit)")
		self.caption_refresh_seconds = 0.5
		self.seconds_since_caption = 0.0
		pygame.init()
		pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
		self.clock = pygame.time.Clock()
		self.rainy_window = RainyWindow(pygame.image.load(self.picture_path), self.window_size)
		self.paused = False
		self.running = True
		self.show_caption()

	def show_caption(self):
		size = len(self.rainy_window.running_drops)
		caption_format = self.caption.format(self.rainy_window.droplets_per_second, size,
		                                     self.rainy_window.blue_shade)
		pygame.display.set_caption(caption_format)

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
			elif event.type == pygame.KEYDOWN:
				self.handle_key(event.key)

	def handle_key(self, key):
		if key == pygame.K_ESCAPE:
			self.running = False
		elif key == pygame.K_SPACE:
			self.paused = not self.paused
		elif key == pygame.K_UP:
			self.rainy_window.change_rainfall(self.rainfall_step)
		elif key == pygame.K_DOWN:
			self.rainy_window.change_rainfall(1.0 / self.rainfall_step)
		elif key == pygame.K_u:
			self.rainy_window.change_blue_shade(self.blue_shade_step)
		elif key == pygame.K_d:
			self.rainy_window.change_blue_shade(-self.blue_shade_step)
		elif key == pygame.K_x:
			self.rainy_window.dry()
		self.show_caption()

	def update(self, seconds):
		if not self.paused:
			self.rainy_window.update(min(seconds, self.longest_frame_seconds))
		self.seconds_since_caption += seconds
		if self.seconds_since_caption >= self.caption_refresh_seconds:
			self.seconds_since_caption = 0.0
			self.show_caption()

	def draw(self):
		glClear(GL_COLOR_BUFFER_BIT)
		self.rainy_window.render()
		pygame.display.flip()

	def run(self):
		while self.running:
			seconds = self.clock.tick(self.frames_per_second) / 1000.0
			self.handle_events()
			self.update(seconds)
			self.draw()
		pygame.quit()


if __name__ == "__main__":
	RainyWindowTest().run()
