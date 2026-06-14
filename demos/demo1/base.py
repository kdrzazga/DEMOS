import arcade
from arcade import Rect
from arcade.types import Color
from arcade import Text
from arcade.color import BLACK, WHITE, AQUA, YELLOW, PINK

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

	def clear_screen(self, color):
		arcade.set_background_color(color)
		bottom = 0
		width = Constants.WIDTH
		height = Constants.HEIGHT
		right = width
		top = bottom + height

		x = width // 2
		y = bottom + height // 2
		r = Rect(0, right, bottom, top, width, height, x, y)
		arcade.draw_rect_filled(r, color=color)

	def blink_write(self, y: int, text: str, start_frame: int, frame: int):

		relative_frame = frame - start_frame
		if relative_frame < 0:
			return

		if relative_frame < 5:
			color = BLACK
		elif relative_frame < 10:
			color = WHITE
		elif relative_frame < 15:
			color = AQUA
		elif relative_frame < 20:
			color = YELLOW
		elif relative_frame < 25:
			color = PINK
		else:
			color = WHITE

		Text(text=text, x=0.1 * Constants.WIDTH, y=y, color=color, font_size=self.font_size
		     , anchor_x="left", font_name="C64 Pro Mono").draw()