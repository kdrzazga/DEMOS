import arcade
from arcade import Rect
from arcade.types import Color

from demos.demo1 import Globals, Constants
from lib.c64 import C64


class Demo1Base(C64):
	def on_update(self, frame, klass):
		if frame == klass.START_FRAME + 1:
			print("New stage", Globals.get_duration(), "[frame", str(frame) + "]")

	def draw_cover(self, color=Constants.LIGHT_BLUE):
		y = 0.1 * Constants.HEIGHT
		height = 0.05 * Constants.HEIGHT
		lb = Color.from_hex_string(color)
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, y, Constants.WIDTH // 2, height)
		arcade.draw_rect_filled(r, color=lb)
