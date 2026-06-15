from arcade import Text
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage10dialog3 import Stage10
from lib.tunnel import TunnelEffect


class Stage11(Demo1Base):
	START_FRAME = Stage10.START_FRAME + 600

	def __init__(self):
		super().__init__()
		lblue = Color.from_hex_string(Constants.LIGHT_BLUE)
		self.tunnel = TunnelEffect(210, Constants.WIDTH, Constants.HEIGHT, lblue)
		self.start_tunnel_frame = 55
		self.base_y = Constants.WIDTH // 2 - 12
		self.X = Constants.WIDTH//4
		self.meet_the_team = Text(
			"MEET THE TEAM:",
			x=self.X,
			y=Constants.WIDTH //2,
			font_name="C64 Pro Mono",
			font_size=12,
			color=Color.from_hex_string(Constants.CYAN)
		)

	def on_update(self, frame, klass):
		relative_frame = frame - Stage11.START_FRAME
		if relative_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		if relative_frame > self.start_tunnel_frame:
			self.tunnel.update()
			for i in range(30):
				self.tunnel.new_dot(i/10)
			if relative_frame > 99 and relative_frame % 35 ==0:
				self.tunnel.dot_size += 1
		# print(relative_frame)

	def on_draw(self, frame):

		super().on_draw(frame)
		relative_frame = frame - Stage11.START_FRAME

		if relative_frame > self.start_tunnel_frame:
			self.tunnel.draw()

		crew = [
			("KOMEK", self.base_y),
			("TOMXX", self.base_y - 24),
			("LEON", self.base_y - 48),
			("TECT", self.base_y - 72),
			("VOID", self.base_y - 96),
			("KD", self.base_y - 120),
			("PHOWIEC", self.base_y - 144),
			("PIANA", self.base_y - 168),
			("DON RAFITO", self.base_y - 192),
			("ARI", self.base_y - 216)
		]

		size = (relative_frame - self.start_tunnel_frame) // 17
		size = min(len(crew), size)

		texts = []
		if relative_frame < self.start_tunnel_frame:
			texts.append(self.meet_the_team)

		intensity = min(255, relative_frame - self.start_tunnel_frame)
		for i in range(size):
			t = Text(
				crew[i][0],
				x=self.X,
				y=crew[i][1],
				font_name="C64 Pro Mono",
				font_size=12,
				color=(intensity, 255, intensity)
			)
			texts.append(t)
			if intensity == 255:
				self.base_y -= 1.5

		for t in texts:
			t.draw()

		if intensity == 255:
			self.draw_cover()
