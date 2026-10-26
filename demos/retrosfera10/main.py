import os
import sys

import pygame
from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_BUFFER_BIT, GL_COLOR_MATERIAL, GL_DEPTH_TEST, GL_FRONT_AND_BACK, GL_LIGHT0,
	GL_LIGHTING, GL_NORMALIZE, GL_SCISSOR_TEST, GL_SMOOTH, glClear, glClearColor, glColorMaterial, glDisable, glEnable,
	glScissor, glShadeModel, glViewport,
)

from lib.demo_phases import Camera
from lib.pygame_demo import PygameDemo
from demos.retrosfera10.models.mainhall import MainHall
from demos.retrosfera10.phases.brzeg_city import BrzegDemoPhase, BrzegTimeline
from demos.retrosfera10.phases.cosmic import CosmicDemoPhase, CosmicTimeline
from demos.retrosfera10.phases.main_hall import MainHallDemoPhase, MainHallTimeline
from demos.retrosfera10.soundtrack import Soundtrack


class FullScreenProfile:
	"""The full-length demo filling the whole screen."""
	def __init__(self):
		self.window_size = (1280, 800)
		self.aspect_ratio = None
		self.field_of_view = 45.0
		self.caption_lead = None

	def cosmic_timeline(self):
		return CosmicTimeline()

	def brzeg_timeline(self):
		return BrzegTimeline()

	def main_hall_phase(self, camera):
		return MainHallDemoPhase(camera)


class ShortsProfile:
	"""The 10-second cut in a 9:16 portrait frame, ending on the logo."""
	def __init__(self, window_height=800):
		self.aspect_ratio = 9 / 16
		self.window_size = (int(window_height * self.aspect_ratio), window_height)
		self.field_of_view = 70.0
		self.caption_lead = 0.5

	def cosmic_timeline(self):
		return CosmicTimeline(space=0.0, letter_frames=1, line_pause_frames=6, caption_fade=0.4, travel_delay=1.0, travel=1.0)

	def brzeg_timeline(self):
		return BrzegTimeline(
			magnify=0.15, landing=0.4, glide=0.45, sway=1.0, sway_count=1, hall_zoom=0.8, hall_orbit=1.2, descent=0.6,
			entry=0.4,
		)

	def main_hall_phase(self, camera):
		timeline = MainHallTimeline(
			walk=1.0, screen_delay=0.3, screen_appear=0.7, caption_hold=0.0, dolls_delay=1.0, logo_zoom_delay=3.0,
		)
		return MainHallDemoPhase(camera, timeline, MainHall(performer_edge_margin=3.0, logo_fill_share=0.85))


class Viewport:
	"""The largest centred area of the given aspect ratio; aspect_ratio None takes the whole display."""
	def __init__(self, display_width, display_height, aspect_ratio=None):
		if aspect_ratio is None:
			self.width, self.height = display_width, display_height
		else:
			self.width = min(display_width, int(display_height * aspect_ratio))
			self.height = min(display_height, int(self.width / aspect_ratio))
		self.left = (display_width - self.width) // 2
		self.bottom = (display_height - self.height) // 2

	def apply(self):
		glViewport(self.left, self.bottom, self.width, self.height)
		glScissor(self.left, self.bottom, self.width, self.height)


class Retrosfera10Demo(PygameDemo):
	def __init__(self, windowed=False, triggered=False, house_style="simple", shorts=False):
		self.house_style = house_style
		self.profile = ShortsProfile() if shorts else FullScreenProfile()
		self.fps = 60
		self.bar_color = (0.0, 0.0, 0.0)
		self.music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "DoubleShit_byRamos.mp3")
		self.music_start_seconds = 7.0
		self.longest_frame = 0.1
		width, height = self.profile.window_size
		super().__init__(width, height, "Retrosfera 10", fps=self.fps, windowed=windowed, triggered=triggered)

	def setup(self):
		display_width, display_height = pygame.display.get_surface().get_size()
		self.viewport = Viewport(display_width, display_height, self.profile.aspect_ratio)
		self.init_gl()
		camera = Camera(self.viewport.width, self.viewport.height, self.profile.field_of_view)
		self.soundtrack = Soundtrack(self.music_path, self.music_start_seconds)
		brzeg_phase = BrzegDemoPhase(camera, self.profile.brzeg_timeline(), house_style=self.house_style)
		self.cosmic_phase = CosmicDemoPhase(camera, self.soundtrack, brzeg_phase.arrival_site, self.profile.cosmic_timeline())
		if self.profile.caption_lead is not None:
			sign_time = self.cosmic_phase.travel_end + brzeg_phase.timeline.sign_time()
			self.cosmic_phase.show_caption_until(sign_time - self.profile.caption_lead)
		self.phases = [self.cosmic_phase, brzeg_phase, self.profile.main_hall_phase(camera)]
		self.phase_index = 0
		self.elapsed = 0.0

	def init_gl(self):
		self.viewport.apply()
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glEnable(GL_NORMALIZE)
		glShadeModel(GL_SMOOTH)

	def clear_bars(self):
		glDisable(GL_SCISSOR_TEST)
		glClearColor(*self.bar_color, 1.0)
		glClear(GL_COLOR_BUFFER_BIT)
		glEnable(GL_SCISSOR_TEST)

	def current_phase(self):
		return self.phases[self.phase_index]

	def advance_phase(self):
		handover = self.current_phase().handover()
		self.phase_index += 1
		self.current_phase().begin(handover)

	def step(self):
		phase = self.current_phase()
		seconds = min(self.longest_frame, self.clock.get_time() / 1000.0)
		self.elapsed += seconds
		phase.update(seconds)
		self.clear_bars()
		phase.render()
		self.cosmic_phase.draw_caption(self.elapsed)
		if phase.done and self.phase_index < len(self.phases) - 1:
			self.advance_phase()

	def handle_event(self, event):
		self.soundtrack.handle_event(event)


if __name__ == "__main__":
	Retrosfera10Demo(shorts=any(arg.lower() in ("s", "shorts", "shorts-view") for arg in sys.argv[1:])).run()
