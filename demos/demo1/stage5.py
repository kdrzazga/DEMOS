import math
import random
import arcade
from arcade import Rect
from arcade.color import WHITE

from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.stage4 import Stage4
from lib.c64 import C64


class Stage5(C64):

	LAST_KnA_ISSUE = 30
	START_FRAME = Stage4.START_FRAME + 270

	def __init__(self):
		super().__init__()
		self.background = arcade.load_texture("demos/demo1/resources/magazine.png")
		arcade.load_font("demos/demo1/resources/HomelandItalic.ttf")

	def on_draw(self, frame):
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, Constants.WIDTH // 2,
		         Constants.HEIGHT // 2)
		arcade.draw_texture_rect(texture=self.background, rect=r)

		rel_frame = frame - Stage5.START_FRAME
		issue_number = rel_frame//5
		if 0 < issue_number <= Stage5.LAST_KnA_ISSUE:
			text = arcade.Text(text="#" + str(issue_number), x=3.5*Constants.WIDTH // 5 - 10, y=3.5*Constants.HEIGHT // 5 + 10
			                   , color=WHITE, font_size=4*self.font_size, font_name="Homeland Italic", anchor_x="left")
			text.draw()
