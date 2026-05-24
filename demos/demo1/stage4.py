import arcade
from arcade import Sprite

from demos.demo1 import Constants
from demos.demo1.stage3 import Stage3
from lib.c64 import C64


class Stage4(C64):
	START_FRAME = Stage3.START_FRAME + 130

	def __init__(self):
		super().__init__()
		self.komoda = Sprite("demos/demo1/resources/komoda.png", center_x=Constants.WIDTH//2
		                     , center_y=-100)
		self.komoda.scale = (0.3, 0.3)


	def on_draw(self, frame):
		self.komoda.center_y += 10
		arcade.draw_sprite(self.komoda)

