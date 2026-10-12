import os

import pygame
from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GL_DEPTH_TEST, GL_FRONT_AND_BACK, GL_LIGHT0, GL_LIGHTING, GL_NORMALIZE,
	GL_SMOOTH, glColorMaterial, glEnable, glShadeModel, glViewport,
)

from lib.demo_phases import Camera
from lib.pygame_demo import PygameDemo
from demos.retrosfera10.phases.brzeg_city import BrzegDemoPhase
from demos.retrosfera10.phases.cosmic import CosmicDemoPhase
from demos.retrosfera10.phases.main_hall import MainHallDemoPhase
from demos.retrosfera10.soundtrack import Soundtrack


class Retrosfera10Demo(PygameDemo):
	def __init__(self, windowed=False, triggered=False, house_style="simple"):
		self.house_style = house_style
		self.fps = 60
		self.field_of_view = 45.0
		self.music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "DoubleShit_byRamos.mp3")
		self.music_start_seconds = 7.0
		self.longest_frame = 0.1
		super().__init__(1280, 800, "Retrosfera 10", fps=self.fps, windowed=windowed, triggered=triggered)

	def setup(self):
		screen_width, screen_height = pygame.display.get_surface().get_size()
		self.init_gl(screen_width, screen_height)
		camera = Camera(screen_width, screen_height, self.field_of_view)
		self.soundtrack = Soundtrack(self.music_path, self.music_start_seconds)
		brzeg_phase = BrzegDemoPhase(camera, house_style=self.house_style)
		cosmic_phase = CosmicDemoPhase(camera, self.soundtrack, brzeg_phase.arrival_site)
		self.phases = [cosmic_phase, brzeg_phase, MainHallDemoPhase(camera)]
		self.phase_index = 0

	def init_gl(self, screen_width, screen_height):
		glViewport(0, 0, screen_width, screen_height)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glEnable(GL_NORMALIZE)
		glShadeModel(GL_SMOOTH)

	def current_phase(self):
		return self.phases[self.phase_index]

	def advance_phase(self):
		handover = self.current_phase().handover()
		self.phase_index += 1
		self.current_phase().begin(handover)

	def step(self):
		phase = self.current_phase()
		phase.update(min(self.longest_frame, self.clock.get_time() / 1000.0))
		phase.render()
		if phase.done and self.phase_index < len(self.phases) - 1:
			self.advance_phase()

	def handle_event(self, event):
		self.soundtrack.handle_event(event)


if __name__ == "__main__":
	Retrosfera10Demo().run()
