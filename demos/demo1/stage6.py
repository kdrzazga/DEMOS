import arcade
from arcade import Rect
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.ghost import Ghost
from demos.demo1.handfloppy import Hand
from demos.demo1.stage5 import Stage5
from lib.c64 import C64


class Stage6(C64):
	START_FRAME = Stage5.START_FRAME + 130

	def __init__(self):
		super().__init__()
		self.hand = Hand()
		self.pinky = Ghost('pinky')
		self.inky = Ghost('inky')
		self.blinky = Ghost('blinky')
		self.clyde = Ghost('clyde')

	def on_draw(self, frame):
		super().draw_background()
		relative_frame = frame - Stage6.START_FRAME
		self.hand.draw(relative_frame)
		self.draw_cover()

		if relative_frame > 250:
			for ghost in (self.pinky, self.inky, self.blinky, self.clyde):
				ghost.draw()

	def on_update(self, frame):
		self.hand.update(frame - Stage6.START_FRAME)
		if self.hand.floppy.center_y < Constants.HEIGHT//2:
			self.hand.move_up()
		else:
			self.hand.move_down()

		for ghost in (self.pinky, self.inky, self.blinky, self.clyde):
			ghost.move()

	def draw_cover(self):
		y = 0.1 * Constants.HEIGHT
		height = 0.05 * Constants.HEIGHT
		lb = Color.from_hex_string(Constants.LIGHT_BLUE)
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, y, Constants.WIDTH // 2, height)
		arcade.draw_rect_filled(r, color=lb)
