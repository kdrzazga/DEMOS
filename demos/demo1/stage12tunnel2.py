import math

import arcade
from arcade.color import BLACK
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage11 import Stage11


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

	def on_update(self, frame, klass):
		if frame == Stage12.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		for sine in self.kurwes:
			sine.update(0.16, self.speed)

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


class IsometricSineTunnel:

	def __init__(self, color: arcade.color.Color, angle_deg=66):
		self.angle_deg = angle_deg
		self.phase = 0
		self.color = color

	def update(self, delta_time, speed=2):
		self.phase += speed * delta_time

	def draw(self, surface_width, surface_height, amplitude, frequency, horizon_x):
		points = []
		angle_rad = math.radians(self.angle_deg)

		for y in range(0, surface_height, 2):
			sine_value = amplitude * math.sin(frequency * (y + self.phase))
			# Convert to isometric projection with x as the sine value
			iso_x, iso_y = self.iso_transform(sine_value + horizon_x, y, angle_rad, surface_width, surface_height)
			points.append((iso_x, iso_y))

		arcade.draw_lines(points, self.color, 1)

	def iso_transform(self, x, y, angle_rad, surface_width, surface_height):
		iso_x = x - y * math.cos(angle_rad)
		iso_y = y * math.sin(angle_rad)

		iso_x += surface_width / 4
		iso_y += surface_height / 4
		return iso_x, iso_y
