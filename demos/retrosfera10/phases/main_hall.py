from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear, glClearColor

from demos.retrosfera10.phases.common import Phase


class MainHallPhase(Phase):
	def __init__(self, camera):
		super().__init__(camera)
		self.background_color = (0.0, 0.0, 0.0)

	def render(self):
		glClearColor(*self.background_color, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
