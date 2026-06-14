import math

import arcade
from arcade import Rect, Sprite
from arcade.color import BLACK, WHITE
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage11 import Stage11
from lib.tunnel import IsometricSineTunnel


class Stage12(Demo1Base):
	START_FRAME = Stage11.START_FRAME + 350

	def __init__(self):
		super().__init__()
		self.kurwes = []
		for i in range(254):
			sine = IsometricSineTunnel(Color(abs(i - 128), 128, int(255 * math.sin(i / 20))), angle_deg=int(370 * i / 255))
			self.kurwes.append(sine)

		self.amplitude = 15
		self.frequency = 0.05
		self.speed = 160
		self.horizon_x = self.width * 0.01

		self.ground = Sprite("demos/demo1/resources/ik/ground.png", center_x=Constants.WIDTH//2, center_y=-205
		                     ,scale=1.33)

	def on_update(self, frame, klass):
		if frame == Stage12.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		for sine in self.kurwes:
			sine.update(0.16, self.speed)

		if frame - Stage12.START_FRAME > 40:
			self.ground.center_y = min(102.0, self.ground.center_y + 3)

	def on_draw(self, frame):
		super().clear_screen(BLACK)
		for sine in self.kurwes:
			sine.draw(
				surface_width=Constants.WIDTH * 2,
				surface_height=Constants.HEIGHT * 2 - 0 * 200,
				amplitude=self.amplitude,
				frequency=self.frequency,
				horizon_x=self.horizon_x
			)
		self.blink_write(0.9*Constants.HEIGHT - 4*12, "READY.", start_frame=Stage12.START_FRAME, frame=frame)
		self.blink_cursor(frame)

		arcade.draw_sprite(self.ground)

	def blink_cursor(self, frame):
		delta = frame % 36
		if delta > 18:
			r = Rect(
				x=0.1 * Constants.WIDTH + 9,
				left=0.1 * Constants.WIDTH,
				y=0.9 * Constants.HEIGHT - 4 * 14,
				right=0.9 * Constants.HEIGHT - 12,
				width=14,
				height=14,
				top=0,
				bottom=0
			)
			arcade.draw_rect_filled(r, color=WHITE)
