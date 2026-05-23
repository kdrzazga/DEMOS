import math
import random

import arcade

from demos.demo1 import Constants
from libs.c64 import C64


class Intro(C64):

	def __init__(self):
		super().__init__()

	def on_update(self, frame):
		cf = random.randint(5, 55)
		cf2 = random.randint(15, 45)
		self.left = 0.1*Constants.WIDTH + cf* math.sin(math.pi/23*frame)
		self.top = 0.9*Constants.HEIGHT + cf2* math.cos(math.pi/13*frame)
		print(frame, end=' ')

	def on_draw(self, frame):
		super().on_draw(frame)

