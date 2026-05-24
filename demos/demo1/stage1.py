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
			str(Stage1.START_FRAME + 20): ["4", '1 PRINT "COMMODORE 64"'],
			str(Stage1.START_FRAME + 30): ["5", '12 POKE 53281,1'],
			str(Stage1.START_FRAME + 40): ["6", 'DATA 10, 20, 10, 20, 30, 40, 50, 255'],
			str(Stage1.START_FRAME + 45): ["7", 'DATA 44, 55, 4, 120, 130, 240, 250, 15'],
			str(Stage1.START_FRAME + 55): ["8", 'DATA 5, 55, 230, 120, 130, 66, 250, 15'],
			str(Stage1.START_FRAME + 65): ["9", 'DATA 44, 55, 230, 120, 130, 240, 250, 15'],
			str(Stage1.START_FRAME + 70): ["10", 'DATA 44, 33, 230, 120, 130, 240, 4, 15'],
			str(Stage1.START_FRAME + 72): ["11", 'DATA 44, 13, 32, 120, 130, 240, 250, 15'],
			str(Stage1.START_FRAME + 77): ["12", 'DATA 24, 55, 4, 43, 130, 240, 55, 43'],
			str(Stage1.START_FRAME + 81): ["13", 'DATA 44, 55, 41, 43, 130, 240, 55, 43'],
			str(Stage1.START_FRAME + 83): ["14", 'DATA 124, 55, 241,124, 55, 241, 43, 130,  43'],
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
