import math
import random
import arcade

from arcade.types import Color

from demos.demo1 import Constants
from lib.c64 import C64


class Intro(C64):

	def __init__(self):
		super().__init__()

		sound = arcade.load_sound("demos/demo1/resources/beat.mp3")
		sound.play(loop=False)

	def on_update(self, frame):
		cf = random.randint(5, 55)
		cf2 = random.randint(15, 45)
		self.left = 0.1*Constants.WIDTH + cf* math.sin(math.pi/23*frame)
		self.top = 0.9*Constants.HEIGHT + cf2* math.cos(math.pi/13*frame)

		if frame > 144:
			self.width -= 3*math.sin(math.pi/frame)
			self.bottom -= 3*math.sin(math.pi/frame)

	def on_draw(self, frame):
		super().on_draw(frame)
		self.write(frame)

	def write(self, frame):

		lines = {
			"150": ["7", "PRESS PLAY ON TAPE"],
			"160": ["8", "LOADING"],
			"188": ["10", "READY."],
			"191": ["11", "RUN"],
		}

		keys = lines.keys()
		lblue = Color.from_hex_string(Constants.LIGHT_BLUE)

		for key in keys:
			key_int = int(key)
			if frame > key_int:
				line_number = int(lines[key][0])
				y = self.line_to_coord(line_number)
				arcade.draw_text(lines[key][1], self.left, y
			                 , color=lblue, font_size=self.font_size, anchor_x="left", font_name="C64 Pro Mono")

