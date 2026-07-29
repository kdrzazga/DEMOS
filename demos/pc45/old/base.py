import arcade
from arcade import Rect
from arcade.color import BLACK
from arcade.types import Color

from demos.pc45 import  Constants


class Pc45Demo:

	background_color = BLACK

	def __init__(self):
		self.frame = 0


	def on_update(self):
		pass

	@classmethod
	def create_bkg_rect(cls):
		x = Constants.WIDTH // 2
		y = Constants.HEIGHT // 2
		r = Rect(0, 0, Constants.WIDTH, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, x, y)
		return r

	@classmethod
	def clear_screen(cls):
		r = Pc45Demo.create_bkg_rect()
		arcade.draw_rect_filled(r, Pc45Demo.background_color)

	@classmethod
	def create_cursor_rect(cls):
		return

	@classmethod
	def blink_cursor(cls, frame:int, color: Color, x=0, y=12, delay=84):
		#print(frame)
		size = 14
		x1 = x
		delta = frame % delay
		height = size // 3

		if delta > delay / 2:
			r = Rect(
				x=x1,
				left=x1,
				y=y - height - 4,
				right=0.9 * Constants.HEIGHT - 12,
				width=2*size//3,
				height=height,
				top=0,
				bottom=0
			)
			arcade.draw_rect_filled(r, color)
