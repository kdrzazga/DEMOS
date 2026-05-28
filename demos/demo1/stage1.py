import math
import arcade

from arcade.types import Color

from demos.demo1 import Constants
from lib.c64 import C64


class Stage1(C64):

	START_FRAME = 200

	def on_update(self, frame):
		self.left -= 34*math.sin(math.pi/frame)
		self.top -= 44*math.sin(math.pi/frame)
		self.font_size -= 0.02

	def on_draw(self, frame):
		super().draw_background()
		self.write1(frame)

		white = Color.from_hex_string(Constants.WHITE)
		if frame > Stage1.START_FRAME + 140:
			arcade.draw_text("SYS 49152", Constants.WIDTH //2, 0.2*Constants.HEIGHT
		                 , color=white, font_size=self.font_size * 2, anchor_x="left", font_name="C64 Pro Mono")


	def write1(self, frame):

		lines = {
			str(Stage1.START_FRAME): ["2", "LIST"],
			str(Stage1.START_FRAME + 20): ["4", '1 REM UP, UP, AND AWAY!'],
			str(Stage1.START_FRAME + 30): ["5", '10 V = 53248 : REM VIC'],
			str(Stage1.START_FRAME + 40): ["6", '11 POKE V+21, 4 : REM ENABLE SPRITE 2'],
			str(Stage1.START_FRAME + 45): ["7", '12 POKE 2042, 13 : REM SPRITE 2 DATA - BL 13'],
			str(Stage1.START_FRAME + 55): ["8", '20 FOR N = 0 TO 62:READ Q:POKE 832+N,Q:NEXT'],
			str(Stage1.START_FRAME + 65): ["9", '30 FOR X = 0 TO 200'],
			str(Stage1.START_FRAME + 70): ["10", '40 POKE V+4, X'],
			str(Stage1.START_FRAME + 72): ["11", '50 POKE V+5, X'],
			str(Stage1.START_FRAME + 77): ["12", '60 NEXT X'],
			str(Stage1.START_FRAME + 81): ["13", '70 GOTO 30'],
			str(Stage1.START_FRAME + 83): ["14", '200 DATA 0, 127, 0, 1, 255, 192, 3, 255, 224, 3, 231, 224'],
			str(Stage1.START_FRAME + 85): ["15", 'DATA 44, 55, 221,44, 48, 180, 240, 58, 43'],
			str(Stage1.START_FRAME + 86): ["16", 'DATA 44, 55, 141, 43, 230, 240, 155, 43, 22, 33'],
			str(Stage1.START_FRAME + 87): ["17", 'DATA 124, 55, 55, 66, 77, 241,124, 55, 241, 43'],
			str(Stage1.START_FRAME + 88): ["18", 'DATA 44, 55, 221, 44, 48, 180, 11, 23, 33, 85, 5'],
			str(Stage1.START_FRAME + 97): ["19", 'DATA 01, 130, 11, 22, 33, 55,  180, 11, 23, 3'],
			str(Stage1.START_FRAME + 102): ["20", 'DATA 84, 100, 22, 33, 55, 41, 22, 33,230,55, END'],
			str(Stage1.START_FRAME + 131): ["22", "READY."]
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
