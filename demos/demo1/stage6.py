import arcade
from arcade import Rect
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.handfloppy import Hand
from demos.demo1.stage5 import Stage5
from lib.animated_sprite import AnimatedSprite
from lib.c64 import C64


class Stage6(C64):
	START_FRAME = Stage5.START_FRAME + 130

	def __init__(self):
		super().__init__()
		self.hand = Hand()
		#TODO self.pacman = AnimatedSprite(Constants.RES_PATH + "pacmen.png")

	def on_draw(self, frame):
		super().draw_background()
		self.hand.draw()
		self.draw_cover()

	def on_update(self, frame):
		if self.hand.floppy.center_y < Constants.HEIGHT//2:
			self.hand.move_up()
		else:
			self.hand.move_down()

	def draw_cover(self):

		y = 0.1 * Constants.HEIGHT
		height = 0.1 * Constants.HEIGHT
		wh = Color.from_hex_string(Constants.LIGHT_BLUE)
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, y, Constants.WIDTH // 2,
		         Constants.HEIGHT * 0.05)
		arcade.draw_rect_filled(r, color=wh)
		arcade.draw_rect_filled(r, color=wh)
