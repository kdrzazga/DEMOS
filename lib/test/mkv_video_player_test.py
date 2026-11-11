import os
import sys

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, RESIZABLE

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from lib.mkv_video_player import MkvVideoPlayer

VIDEO_PATH = os.path.join(PROJECT_ROOT, "demos", "retro_neons", "resources", "meet-the-team.mkv")


class MkvVideoPlayerTestApp:

	def __init__(self):
		self.window_size = (1280, 720)
		self.refresh_rate = 60
		pygame.display.init()
		self.window = pygame.display.set_mode(self.window_size, RESIZABLE)
		pygame.display.set_caption("MkvVideoPlayer test")
		self.clock = pygame.time.Clock()
		self.player = MkvVideoPlayer(VIDEO_PATH, loop=True)
		self.running = True

	def run(self):
		while self.running:
			self.handle_events()
			self.player.update()
			self.draw()
			self.clock.tick(self.refresh_rate)
		self.player.close()
		pygame.quit()

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				self.running = False

	def draw(self):
		self.window.fill((0, 0, 0))
		picture_rectangle = self.letterboxed_picture_rectangle()
		scaled_picture = pygame.transform.smoothscale(self.player.surface, picture_rectangle.size)
		self.window.blit(scaled_picture, picture_rectangle)
		pygame.display.flip()

	def letterboxed_picture_rectangle(self):
		window_width, window_height = self.window.get_size()
		scale = min(window_width / self.player.width, window_height / self.player.height)
		picture_width = max(1, round(self.player.width * scale))
		picture_height = max(1, round(self.player.height * scale))
		return pygame.Rect((window_width - picture_width) // 2, (window_height - picture_height) // 2,
		                   picture_width, picture_height)


if __name__ == "__main__":
	MkvVideoPlayerTestApp().run()
