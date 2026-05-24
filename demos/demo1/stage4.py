import math
import random
import arcade
from arcade import Rect

from arcade.types import Color

from demos.demo1 import Constants
from lib.c64 import C64


class Stage4(C64):

	START_FRAME = 800

	def __init__(self):
		super().__init__()

		self.background = arcade.load_texture("demos/demo1/resources/magazine.png")

	def on_draw(self, frame):
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, Constants.WIDTH // 2,
		         Constants.HEIGHT // 2)
		arcade.draw_texture_rect(texture=self.background, rect=r)
