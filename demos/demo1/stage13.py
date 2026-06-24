import math
import arcade

from arcade import Rect
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage12ikplus import Stage12


class Stage13(Demo1Base):
	START_FRAME = Stage12.START_FRAME + 600

	def __init__(self):
		super().__init__()
		self.font_color = "ffffff"
		self.bg_color = "000000"
		self.t = 0

	def on_update(self, frame, klass):
		if frame == Stage13.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
		else:
			self.t += 0.05
			self.change_color()

	def on_draw(self, frame: int):
		self.clear_screen(Color.from_hex_string(self.font_color))
		super().on_draw2(frame, color=self.font_color, bg_color=self.bg_color)

		relative_frame = frame - Stage13.START_FRAME

		if relative_frame > 150:
			height = min(relative_frame-150, 150)
			x = 0 + self.width // 2
			y = Constants.HEIGHT // 2
			r = Rect(self.left, Constants.WIDTH, self.bottom, self.top, Constants.WIDTH, height, x, y)
			arcade.draw_rect_filled(r, color=Color.from_hex_string(self.font_color))

		self.blink_cursor(relative_frame)

	def change_color(self, amplitude=127.5, offset=127.5):
		r = int(amplitude * math.sin(self.t) + offset)
		g = int(amplitude * math.sin(self.t + 2 * math.pi / 3) + offset)
		b = int(amplitude * math.sin(self.t + 4 * math.pi / 3) + offset)
		r = max(0, min(255, r))
		g = max(0, min(255, g))
		b = max(0, min(255, b))
		self.font_color = f"{r:02x}{g:02x}{b:02x}"

	def blink_cursor(self, frame):
		delta = frame % 84
		if delta > 84/2:
			r = Rect(
				x=0.1 * Constants.WIDTH + 9,
				left=0.1 * Constants.WIDTH,
				y=0.9 * Constants.HEIGHT - 8 * 14 - 7,
				right=0.9 * Constants.HEIGHT - 12,
				width=16,
				height=16,
				top=0,
				bottom=0
			)
			arcade.draw_rect_filled(r, color=Color.from_hex_string(self.font_color))