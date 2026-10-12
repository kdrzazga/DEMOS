import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, FULLSCREEN, K_ESCAPE, KEYDOWN, MOUSEBUTTONDOWN, OPENGL, QUIT

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.base_demo import BaseDemo
from demos.pixeloveole3.logo_phases import build_logo_phases
from demos.pixeloveole3.logo_show import LogoShow


class PixeloveOle3(BaseDemo):

	def __init__(self, width, height, title, fps=60, opengl=True,
				 windowed=False, triggered=False):
		super().__init__(windowed=windowed, triggered=triggered)
		self.width = width
		self.height = height
		self.title = title
		self.fps = fps
		self.opengl = opengl
		self.clock = pygame.time.Clock()
		self.longest_frame = 0.1

		pygame.init()
		pygame.mouse.set_visible(False)
		self._init_display()
		self.show = LogoShow(self.width, self.height) if self.opengl else None
		self.phases = build_logo_phases(self.show) if self.show else []
		self.phase_index = 0
		if self.phases:
			self.current_phase().begin(None)

	def current_phase(self):
		return self.phases[self.phase_index]

	def advance_phase(self):
		handover = self.current_phase().handover()
		self.phase_index += 1
		self.current_phase().begin(handover)

	def step(self, delta_seconds):
		phase = self.current_phase()
		phase.update(min(self.longest_frame, delta_seconds))
		phase.render()
		if phase.done and self.phase_index < len(self.phases) - 1:
			self.advance_phase()

	def _init_display(self):
		flags = DOUBLEBUF
		if self.opengl:
			flags |= OPENGL
		if self.windowed:
			pygame.display.set_mode((self.width, self.height), flags)
		else:
			pygame.display.set_mode((0, 0), flags | FULLSCREEN)
		self.width, self.height = pygame.display.get_surface().get_size()
		pygame.display.set_caption(self.title)

	def run(self):
		running = True
		while running:
			delta_seconds = self.clock.tick(self.fps) / 1000.0
			for event in pygame.event.get():
				if event.type == QUIT:
					running = False
				elif event.type == KEYDOWN and event.key == K_ESCAPE:
					running = False
				elif event.type == MOUSEBUTTONDOWN:
					self.trigger()
			if self.show:
				if self.paused:
					self.show.render_blank()
				else:
					self.step(delta_seconds)
			pygame.display.flip()
		pygame.quit()


if __name__ == "__main__":
	PixeloveOle3(1280, 720, "Pixelove Ole 3", windowed=True).run()
