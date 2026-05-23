import arcade
from arcade import Rect
from arcade.types import Color

from demos.demo1 import Constants


class C64:

	def __init__(self):
		arcade.load_font("lib/resources/C64_Pro_Mono-STYLE.ttf")
		self.top = 0
		self.font_size = 12

		self.header_x = 0.5 * Constants.WIDTH

		self.left = 0.1 * Constants.WIDTH
		self.bottom = 0.1 * Constants.HEIGHT
		self.width = 0.8 * Constants.WIDTH
		self.height = 0.8 * Constants.HEIGHT
		self.right = self.left + self.width
		self.top = self.bottom + self.height

	def on_draw(self, frame):
		lblue = Color.from_hex_string(Constants.LIGHT_BLUE)

		self.draw_background()
		y = self.line_to_coord(2)

		arcade.draw_text("**** COMMODORE 64 BASIC V2 ****", self.header_x, y
		                 , color=lblue, font_size=self.font_size, anchor_x="center", font_name="C64 Pro Mono")
		y = self.line_to_coord(4)
		arcade.draw_text(" 64K RAM SYSTEM  38911 BASIC BYTES FREE ", self.header_x, y
		                 , color=lblue, font_size=self.font_size, anchor_x="center", font_name="C64 Pro Mono")
		y = self.line_to_coord(6)
		arcade.draw_text("READY.", self.left, y
		                 , color=lblue, font_size=self.font_size, anchor_x="left", font_name="C64 Pro Mono")

	def draw_background(self):
		blue = Color.from_hex_string(Constants.BLUE)
		x = self.left + self.width // 2
		y = self.bottom + self.height // 2
		r = Rect(self.left, self.right, self.bottom, self.top, self.width, self.height, x, y)
		arcade.draw_rect_filled(r, color=blue)

	def line_to_coord(self, line_number) -> int:
		return self.top - line_number * self.font_size*1.5
