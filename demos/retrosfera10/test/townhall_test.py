import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, K_ESCAPE, K_SPACE, KEYDOWN, MOUSEWHEEL, OPENGL, QUIT
from OpenGL.GL import (
	GL_AMBIENT, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_DIFFUSE, GL_LIGHT0, GL_LIGHTING,
	GL_MODELVIEW, GL_POSITION, GL_PROJECTION, GL_QUADS, GL_SMOOTH, glBegin, glClear, glClearColor, glColor3f,
	glDisable, glEnable, glEnd, glLightfv, glLoadIdentity, glMatrixMode, glPopMatrix, glPushMatrix, glRotatef,
	glShadeModel, glTranslatef, glVertex3f, glViewport,
)
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.retrosfera10.models.townhall import TownHall


class Ground:
	def __init__(self, half_size, color):
		self.half_size = half_size
		self.color = color

	def draw(self):
		glDisable(GL_LIGHTING)
		glColor3f(*self.color)
		glBegin(GL_QUADS)
		glVertex3f(-self.half_size, -0.01, -self.half_size)
		glVertex3f(self.half_size, -0.01, -self.half_size)
		glVertex3f(self.half_size, -0.01, self.half_size)
		glVertex3f(-self.half_size, -0.01, self.half_size)
		glEnd()


class OrbitCamera:
	def __init__(self, distance, height, target_height, minimum_distance, maximum_distance):
		self.distance = distance
		self.height = height
		self.target_height = target_height
		self.minimum_distance = minimum_distance
		self.maximum_distance = maximum_distance

	def zoom(self, steps):
		self.distance = max(self.minimum_distance, min(self.maximum_distance, self.distance - steps * 3.0))

	def apply(self, aspect):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective(40.0, aspect, 0.5, 500.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		gluLookAt(0.0, self.height * self.distance / 75.0, self.distance, 0.0, self.target_height, 0.0, 0.0, 1.0, 0.0)


class TownHallTestApp:
	def __init__(self, width=1280, height=800, degrees_per_second=18.0, camera_distance=75.0, caption="Town hall test"):
		self.width = width
		self.height = height
		self.degrees_per_second = degrees_per_second
		self.angle = 0.0
		self.paused = False
		self.running = True
		self.sky_color = (0.55, 0.72, 0.92)
		self.light_direction = (0.55, 0.85, 0.65, 0.0)
		self.caption = caption
		self.camera = OrbitCamera(camera_distance, 28.0, 12.0, 25.0, 320.0)
		self.ground = Ground(220.0, (0.42, 0.42, 0.4))
		self.model = None

	def create_model(self):
		return TownHall()

	def setup_gl(self):
		glViewport(0, 0, self.width, self.height)
		glClearColor(*self.sky_color, 1.0)
		glEnable(GL_DEPTH_TEST)
		glShadeModel(GL_SMOOTH)
		glEnable(GL_LIGHT0)
		glLightfv(GL_LIGHT0, GL_AMBIENT, (0.42, 0.42, 0.45, 1.0))
		glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.72, 0.7, 0.66, 1.0))

	def handle_events(self):
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				self.running = False
			elif event.type == KEYDOWN and event.key == K_SPACE:
				self.paused = not self.paused
			elif event.type == MOUSEWHEEL:
				self.camera.zoom(event.y)

	def update(self, seconds):
		if not self.paused:
			self.angle = (self.angle + self.degrees_per_second * seconds) % 360.0

	def render(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply(self.width / self.height)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		self.ground.draw()
		glPushMatrix()
		glRotatef(self.angle, 0.0, 1.0, 0.0)
		center = self.model.center
		glTranslatef(-center.x, -center.y, -center.z)
		self.model.draw()
		glPopMatrix()

	def run(self):
		pygame.init()
		pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
		pygame.display.set_caption(f"{self.caption} - SPACE pause, wheel zoom, ESC quit")
		self.setup_gl()
		self.model = self.create_model()
		clock = pygame.time.Clock()
		while self.running:
			self.handle_events()
			self.update(clock.tick(60) / 1000.0)
			self.render()
			pygame.display.flip()
		self.model.release()
		pygame.quit()


if __name__ == "__main__":
	TownHallTestApp().run()
