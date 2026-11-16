import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
from pygame.locals import DOUBLEBUF, OPENGL

from lib.graffitti.kna2.komoda_amiga_plus_animation import KomodaAmigaPlusAnimation


class GraffitiKna2TestApp:

	def __init__(self):
		self.window_size = (1280, 720)
		self.frames_per_second = 60
		pygame.init()
		pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
		pygame.display.set_caption(
			"Graffiti - KOMODA AND AMIGA PLUS   [SPACE restart, P pause, G finished, B blink, W blink wave, ESC quit]")
		self.animation = KomodaAmigaPlusAnimation(self.window_size)
		self.clock = pygame.time.Clock()
		self.key_actions = {
			pygame.K_SPACE: self.animation.restart,
			pygame.K_p: self.animation.toggle_pause,
			pygame.K_g: self.animation.show_finished,
			pygame.K_b: self.animation.blink,
			pygame.K_w: self.animation.blink_wave,
		}

	def _handle_events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return False
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return False
				if event.key in self.key_actions:
					self.key_actions[event.key]()
		return True

	def run(self):
		while self._handle_events():
			self.animation.update(self.clock.tick(self.frames_per_second) / 1000.0)
			self.animation.render()
			pygame.display.flip()
		pygame.quit()


if __name__ == "__main__":
	GraffitiKna2TestApp().run()
