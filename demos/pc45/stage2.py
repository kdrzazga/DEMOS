import math
import os

import pygame
from OpenGL.GL import *

try:
	from effects.portrait import ExtrudedPhoto
except ModuleNotFoundError:
	from demos.pc45.effects.portrait import ExtrudedPhoto


class Stage2:

	FPS = 60
	PORTRAIT_IMAGE = "team/DonEstridge.png"
	PORTRAIT_DEPTH_PX = 10
	HALF_HEIGHT = 0.9
	CAM_Z = -3.0
	YAW = 24.0
	YAW_SPEED = 0.5

	def __init__(self, win_w, win_h, res_path, fov):
		self.frame = 0
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)
		self.portrait = ExtrudedPhoto(os.path.join(res_path, self.PORTRAIT_IMAGE),
		                              self.HALF_HEIGHT, self.PORTRAIT_DEPTH_PX)

	def render(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, self.CAM_Z)
		angle = self.YAW * math.sin(self.frame / self.FPS * self.YAW_SPEED)
		glRotatef(angle, 0.0, 1.0, 0.0)
		self.portrait.draw()
		self.frame += 1

	@property
	def done(self):
		return False

	def destroy(self):
		self.portrait.destroy()
