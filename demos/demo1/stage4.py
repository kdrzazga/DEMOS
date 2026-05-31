import math

import arcade
from arcade import Sprite

from demos.demo1 import Constants
from demos.demo1.stage3 import Stage3
from lib.c64 import C64


class Stage4(C64):
	START_FRAME = Stage3.START_FRAME + 130

	def __init__(self):
		super().__init__()
		path = Constants.RES_PATH + "kna/"
		self.komoda = Sprite(path + "komoda.png", center_x=Constants.WIDTH // 2, center_y=-100)
		self.ampersand = Sprite(path + "ampersand.png", center_x=Constants.WIDTH // 2, center_y=-200)
		self.amiga = Sprite(path + "amiga.png", center_x=Constants.WIDTH // 2, center_y=-300)
		self.plus = Sprite(path + "plus.png", center_x=Constants.WIDTH // 2, center_y=-400)
		self.komoda.scale = (0.3, 0.3)

	def on_draw(self, frame):

		for sprite in (self.komoda, self.ampersand, self.amiga, self.plus):
			sprite.angle += 0.3
			sprite.center_y += 6
			coeff = (frame - Stage4.START_FRAME) * math.pi/50
			sprite.scale = (0.3 * math.sin(coeff) + 0.5, 0.3 * math.sin(coeff) + 0.3)
			arcade.draw_sprite(sprite)

