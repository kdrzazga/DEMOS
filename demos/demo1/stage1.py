import math
import arcade
from arcade import Sprite

from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.base import Demo1Base


class Stage1(Demo1Base):

	START_FRAME = 200

	def __init__(self):
		super().__init__()
		self.handbook = arcade.load_texture(Constants.RES_PATH + 'c64handbook.png')
		self.baloon = Sprite(Constants.RES_PATH + "baloon.png")
		self.baloon.center_x = Constants.WIDTH//2
		self.baloon.center_y = Constants.HEIGHT//2

	def on_update(self, frame, klass):
		super().on_update(frame, klass)
		self.left -= 34*math.sin(math.pi/frame)
		self.top -= 44*math.sin(math.pi/frame)
		self.font_size -= 0.02

	def on_draw(self, frame):
		super().draw_background()
		relative_frame = frame - Stage1.START_FRAME

		white = Color.from_hex_string(Constants.WHITE)
		if relative_frame > 140:
			caption = arcade.Text(text="SYS 49152", x=Constants.WIDTH // 2, y=0.2*Constants.HEIGHT, color=white,
			            font_size=self.font_size * 2, anchor_x="left", font_name="C64 Pro Mono")
			caption.draw()

		r = self.create_bkg_rect()

		if relative_frame in (8, 9, 10, 11, 23, 24, 25) or 30 < relative_frame < 40 or 105 < relative_frame < 125:
			arcade.draw_texture_rect(texture=self.handbook, rect=r)
		else:
			self.write1(relative_frame)

		if relative_frame > 140:
			arcade.draw_sprite(self.baloon)
			if relative_frame % 6 ==0:
				scale = self.baloon.scale_x + 1
				self.baloon.scale = (scale, scale)

	def write1(self, frame):

		lines = {
			str(0): ["2", "LIST"],
			str(20): ["4", '1 REM UP, UP, AND AWAY!'],
			str(30): ["5", '10 V = 53248 : REM VIC'],
			str(40): ["6", '11 POKE V+21, 4 : REM ENABLE SPRITE 2'],
			str(45): ["7", '12 POKE 2042, 13 : REM SPRITE 2 DATA - BL 13'],
			str(55): ["8", '20 FOR N = 0 TO 62:READ Q:POKE 832+N,Q:NEXT'],
			str(65): ["9", '30 FOR X = 0 TO 200'],
			str(70): ["10", '40 POKE V+4, X'],
			str(72): ["11", '50 POKE V+5, X'],
			str(77): ["12", '60 NEXT X'],
			str(81): ["13", '70 GOTO 30'],
			str(83): ["14", '200 DATA 0, 127, 0, 1, 255, 192, 3, 255, 224'], #, 3, 231, 224'],
			str(85): ["15", 'DATA 44, 55, 221,44, 48, 180, 240, 58, 43'],
			str(86): ["16", 'DATA 44, 55, 141, 43, 230, 240, 155, 43, 22, 33'],
			str(87): ["17", 'DATA 124, 55, 55, 66, 77, 241,124, 55, 241, 43'],
			str(88): ["18", 'DATA 44, 55, 221, 44, 48, 180, 11, 23, 33, 85, 5'],
			str(97): ["19", 'DATA 01, 130, 11, 22, 33, 55,  180, 11, 23, 3'],
			str(102): ["20", 'DATA 84, 100, 22, 33, 55, 41, 22, 33,230,55, END'],
			str(131): ["22", "READY."]
		}

		keys = lines.keys()
		lblue = Color.from_hex_string(Constants.LIGHT_BLUE)

		for key in keys:
			key_int = int(key)
			if frame > key_int:
				line_number = int(lines[key][0])
				y = self.line_to_coord(line_number)
				arcade.Text(text=lines[key][1], x=self.left, y=y, color=lblue, font_size=self.font_size
				            , anchor_x="left", font_name="C64 Pro Mono")
