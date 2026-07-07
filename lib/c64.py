import arcade
from arcade import Rect, Text
from arcade.types import Color

from demos.demo1 import Constants


class C64:

	def __init__(self, screen_width, screen_height):
		arcade.load_font("lib/resources/C64_Pro_Mono-STYLE.ttf")
		self.top = 0
		self.font_size = 12
		self.screen_width = screen_width
		self.screen_height = screen_height

		self.header_x = 0.5 * screen_width

		self.left = 0.1 * screen_width
		self.bottom = 0.1 * screen_height
		self.width = 0.8 * screen_width
		self.height = 0.8 * screen_height
		self.right = self.left + self.width
		self.top = self.bottom + self.height
		self.header1 = ""

	def on_draw(self, frame):
		self.on_draw2(frame, Constants.LIGHT_BLUE, Constants.BLUE)

	def on_draw2(self, frame, color: str, bg_color: str):
		#print(color)
		lblue = Color.from_hex_string(color)

		self.draw_background(bg_color)

		y = self.line_to_coord(2)
		Text(text="**** COMMODORE 64 BASIC V2 ****", x=self.header_x, y=y, color=lblue,
		            font_size=self.font_size, anchor_x="center", font_name="C64 Pro Mono").draw()

		y = self.line_to_coord(4)
		Text(text=" 64K RAM SYSTEM  38911 BASIC BYTES FREE ", x=self.header_x, y=y, color=lblue,
		     font_size=self.font_size, anchor_x="center", font_name="C64 Pro Mono").draw()

		y = self.line_to_coord(6)
		Text(text="READY.", x=self.left, y=y, color=lblue, font_size=self.font_size, anchor_x="left"
		     , font_name="C64 Pro Mono").draw()

	def draw_background(self, color=Constants.BLUE):
		blue = Color.from_hex_string(color)
		r = self.create_bkg_rect()
		arcade.draw_rect_filled(r, color=blue)

	def create_bkg_rect(self):
		x = self.left + self.width // 2
		y = self.bottom + self.height // 2
		r = Rect(self.left, self.right, self.bottom, self.top, self.width, self.height, x, y)
		return r

	def line_to_coord(self, line_number) -> int:
		return self.top - line_number * self.font_size*1.5

	def fullscreen(self):
		self.left = 0
		self.bottom = 0.1*self.screen_height
		self.width = self.screen_width
		self.height = 2*self.screen_height
		self.right = self.left + self.width
		self.top = self.bottom + self.height

	def blink_cursor(self, frame, color, x=0, y=4*14, delay=84):

		size = 14
		x1 = 0.1 * Constants.WIDTH + x*size
		delta = frame % delay
		if delta > delay/2:
			r = Rect(
				x=x1+9,
				left=x1,
				y=0.9 * Constants.HEIGHT - y,
				right=0.9 * Constants.HEIGHT - 12,
				width=size,
				height=size+1,
				top=0,
				bottom=0
			)
			arcade.draw_rect_filled(r, color)
