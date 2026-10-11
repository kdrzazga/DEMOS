from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear, glClearColor

from demos.retrosfera10.models.mainhall import MainHall
from demos.retrosfera10.models.townhall import Vector3
from demos.retrosfera10.phases.common import Easing, Light, Phase


class MainHallTimeline:
	def __init__(self, walk=18.0):
		self.walk = walk


class MainHallPhase(Phase):
	def __init__(self, camera, timeline=None):
		super().__init__(camera)
		self.timeline = timeline or MainHallTimeline()
		self.background_color = (0.0, 0.0, 0.0)
		self.light = Light(Vector3(0.3, 1.0, 0.45), (0.56, 0.54, 0.5, 1.0), (0.5, 0.48, 0.44, 1.0))
		self.hall = MainHall()
		far_wall = -self.hall.half_length
		self.start_eye = Vector3(0.0, 2.6, self.hall.half_length - 0.5)
		self.end_eye = Vector3(0.0, 1.9, self.hall.stage_front() + 9.0)
		self.start_target = Vector3(0.0, 2.6, far_wall)
		self.end_target = Vector3(0.0, 1.6, far_wall)

	def render(self):
		glClearColor(*self.background_color, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply_projection(0.1, 200.0)
		walk = Easing.smooth(self.elapsed / self.timeline.walk)
		eye = Easing.blend(self.start_eye, self.end_eye, walk)
		target = Easing.blend(self.start_target, self.end_target, walk)
		self.camera.look(eye, target, Vector3.up())
		self.light.apply()
		self.hall.draw()
