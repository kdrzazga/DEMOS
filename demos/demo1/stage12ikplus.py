import math

import arcade
from arcade import Rect, Sprite
from arcade.color import WHITE
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage11team import Stage11
from lib.tunnel import IsometricSineTunnel


class Stage12(Demo1Base):
	START_FRAME = Stage11.START_FRAME + 350

	def __init__(self):
		super().__init__()
		self.bkg_color = Color.from_hex_string("000000")
		self.kurwes = []
		for i in range(254):
			g = abs(int(252 * math.sin(i / 20)) + 2)
			b = abs(i - 128)
			sine = IsometricSineTunnel(Color(255, g, b), angle_deg=int(370 * i / 255))
			self.kurwes.append(sine)

		self.amplitude = 15
		self.frequency = 0.05
		self.speed = 160
		self.horizon_x = self.width * 0.01

		self.ground = Sprite("demos/demo1/resources/ik/ground.png", center_x=Constants.WIDTH//2, center_y=-205
		                     ,scale=1.33)
		self.tree = Sprite("demos/demo1/resources/ik/tree.png", center_x=Constants.WIDTH*1.3, center_y=305
		                     ,scale=2.5)
		self.grandpa = Sprite("demos/demo1/resources/ik/ik-grandpa.png", center_x=Constants.WIDTH * 0.6, center_y=-205
		                     ,scale=0.6)
		self.tori = Sprite("demos/demo1/resources/ik/tori.png", center_x=Constants.WIDTH * 0.25, center_y=305
		                     ,scale=2.5)

		self.balls = [Ball() for _ in range(20)]

	def on_update(self, frame, klass):
		realtive_frame = frame - Stage12.START_FRAME
		if realtive_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		for sine in self.kurwes:
			sine.update(0.16, self.speed)

		if realtive_frame > 40:
			self.ground.center_y = min(102.0, self.ground.center_y + 3)
			if realtive_frame > 70:
				self.tree.center_x = max(685.0, self.tree.center_x - 3)
				r = self.bkg_color.r
				#print(r, end=' ')
				if realtive_frame % 3 == 0:
					r = min(200, r + 3)

				r_hex = f"{r:02x}"
				#print(r_hex)
				self.bkg_color = Color.from_hex_string(r_hex + "0000")

				if realtive_frame == 130:
					self.speed = -self.speed

				elif realtive_frame > 150:
					self.speed += 1
					self.grandpa.center_y = min(330.0, self.grandpa.center_y + 3)

	def on_draw(self, frame):
		super().clear_screen(self.bkg_color)
		relative_frame = frame - Stage12.START_FRAME

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

		for sprite in (self.grandpa, self.ground, self.tree):
			arcade.draw_sprite(sprite)

		if relative_frame > 150:
			arcade.draw_sprite(self.tori)

		if relative_frame > 150:
			self.speed += 1
			# print(len(self.balls))
			for ball in self.balls:
				ball.move()
				ball.draw()
				# print(ball.x, ball.y, end=' | ')
				# print()

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


class Ball:

	COUNT = 0

	def __init__(self):
		Ball.COUNT += 1
		Ball.SIZE = 15
		Ball.GROUND_ZERO = 0.1 * Constants.HEIGHT

		colors = (Constants.BLACK, Constants.CYAN, Constants.WHITE, Constants.YELLOW, Constants.GREEN, Constants.LIGHT_BLUE)
		self.color = Color.from_hex_string(colors[Ball.COUNT % len(colors)])

		self.x = - 10 * Ball.COUNT * Ball.SIZE
		self.y = Ball.GROUND_ZERO

		self.speed = 11 + (Ball.COUNT % 3)*3

		self.magnitude = 30 + (15+5*Ball.COUNT)*math.sin(2*math.pi / Ball.COUNT)

	def move(self):
		self.y = Ball.GROUND_ZERO + self.magnitude * abs(math.sin(self.x * 3.141 / (Constants.HEIGHT // 2)))
		self.x += self.speed

		if self.x > 1.2 *Constants.WIDTH:
			self.x = - Ball.COUNT * Ball.SIZE

	def draw(self):
		arcade.draw_circle_filled(self.x, self.y, Ball.SIZE, self.color)
