import arcade
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
		self.X = Constants.WIDTH//5
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
			if relative_frame > 111 and relative_frame % 80 == 0:
				self.tunnel.dot_size += 1
			if relative_frame > 250 and relative_frame % 81 == 0:
				self.tunnel.dot_size += 2
			if relative_frame > 580:
				self.tunnel.dot_size += 1
		# print(relative_frame)

	def on_draw(self, frame):

		super().on_draw(frame)
		relative_frame = frame - Stage11.START_FRAME

		if relative_frame > self.start_tunnel_frame:
			self.tunnel.draw()
			#print(relative_frame)

		crew = self.get_part_of_crew(relative_frame)

		size = (relative_frame - self.get_section_start(relative_frame)) // 17
		size = min(len(crew), size)

		texts = []
		if relative_frame < self.start_tunnel_frame:
			texts.append(self.meet_the_team)
		else:
			if self.start_tunnel_frame + 100 < relative_frame < self.start_tunnel_frame + 422:
				pass#arcade.draw_sprite(self.akm)

		intensity = min(255, (relative_frame - self.start_tunnel_frame) // 3)
		if intensity < 0:
			intensity = 0
		c = (intensity, 255, intensity)

		caption_x = self.X

		if size > 11:
			caption_x += Constants.WIDTH//5

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
			if relative_frame > 695:
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


	def get_part_of_crew(self, rel_frame):
		if rel_frame < 230:
			team = [
				("KOMEK", self.base_y),
				("TOMXX", self.base_y - 2 * 14),
				("LEON", self.base_y - 4 * 14),
				("TECT", self.base_y - 6 * 14),
				("VOID", self.base_y - 8 * 14),
				("KD", self.base_y - 10 * 14),
				("PHOWIEC", self.base_y - 12 * 14),
				("PIANA", self.base_y - 14 * 14),
				("DON RAFITO", self.base_y - 16 * 14)
			]

		elif rel_frame < 2*230:
			team = [
				("ARI", self.base_y - 2 * 14),
				("BESZCZA", self.base_y - 4 * 14),
				("LOUIE", self.base_y - 6 * 14),
				("RETRO CHLOP", self.base_y - 8 * 14),
				("RAZOR", self.base_y - 10 * 14),
				("ERIK", self.base_y - 12 * 14),
				("SLEEVA", self.base_y - 14 * 14),
				("RETRO BAJTEL", self.base_y - 16 * 14),
				("JACKAL", self.base_y - 18 * 14)
			]

		else:
			team = [
				("BOBER8BIT", self.base_y - 2 * 14),
				("EDIMAN", self.base_y - 4 * 14),
				("ZSOMBOR", self.base_y - 6 * 14),
				("HERY", self.base_y - 8 * 14),
				("ENEY666", self.base_y - 10 * 14),
				("JACKMF", self.base_y - 12 * 14),
				("DRAKON", self.base_y - 14 * 14),
				("SOBCZYK", self.base_y - 16 * 14),
				("DEADMAN", self.base_y - 18 * 14)
			]
		return team

	def get_section_start(self, rel_frame):
		if rel_frame < 230:
			return self.start_tunnel_frame
		elif rel_frame < 2 * 230:
			return 230
		else:
			return 2 * 230

	def compute_caption_x(self, i):
		if i < 11:
			return self.X
		elif i < 22:
			return self.X + Constants.WIDTH//4
		else:
			return self.X + Constants.WIDTH //2
