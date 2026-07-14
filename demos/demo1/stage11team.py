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
		self.base_y = 26*14
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
			for i in range(15):
				self.tunnel.new_dot(i/10)
			if relative_frame > 111 and relative_frame % 35 == 0:
				self.tunnel.dot_size += 1
			if relative_frame > 260:
				self.tunnel.dot_size += 1
		# print(relative_frame)

	def on_draw(self, frame):

		super().on_draw(frame)
		relative_frame = frame - Stage11.START_FRAME

		if relative_frame > self.start_tunnel_frame:
			self.tunnel.draw()

		crew = [
			("KOMEK", self.base_y),
			("TOMXX", self.base_y - 2*14),
			("LEON", self.base_y - 4*14),
			("TECT", self.base_y - 6*14),
			("VOID", self.base_y - 8*14),
			("KD", self.base_y - 10*14),
			("PHOWIEC", self.base_y - 12*14),
			("PIANA", self.base_y - 14*14),
			("DON RAFITO", self.base_y - 16*14),
			("ARI", self.base_y - 18*14)
		]

		size = (relative_frame - self.start_tunnel_frame) // 17
		size = min(len(crew), size)

		texts = []
		if relative_frame < self.start_tunnel_frame:
			texts.append(self.meet_the_team)

		intensity = min(255, relative_frame - self.start_tunnel_frame)
		if intensity < 0:
			intensity = 0
		c = (intensity, 255, intensity)
		for i in range(size):
			t = Text(
				crew[i][0],
				x=self.X,
				y=crew[i][1],
				font_name="C64 Pro Mono",
				font_size=12,
				color=c,
				anchor_x="left",
				anchor_y="center"
			)
			texts.append(t)
			if intensity == 255:
				self.base_y -= 1.5

		for t in texts:
			t.draw()

		if len(texts) > 1: # skip'meet the team' text
			x = (self.X + len(texts[-1].text) * 14 - 4*14) // 14
			y = 0.9 * Constants.HEIGHT - texts[-1].y -2
			if y > 0:
				self.blink_cursor(relative_frame, c, x, y, 20)

		if intensity == 255:
			self.draw_cover()
