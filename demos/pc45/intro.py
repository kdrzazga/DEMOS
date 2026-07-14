import arcade
from arcade import Text
from arcade.color import WHITE

from demos.pc45 import Constants
from demos.pc45.base import Pc45Demo
from lib.beeptyper import Typer


class Intro(Pc45Demo):

	def __init__(self):

		super().__init__()
		self.font_size = 16
		font_name = "Mx437_Acer710_Mono"
		self.beep_typer = Typer(0, Constants.HEIGHT - self.font_size, font_name+".ttf", font_name, self.font_size, WHITE)
		arcade.load_font("lib/resources/Mx437_Acer710_Mono.ttf")
		self.cursor_x = self.font_size
		self.cursor_y = Constants.HEIGHT - self.font_size
		self.cursor_color = arcade.color.GREEN

	def on_update(self, frame):
		pass

	def on_draw(self, frame:int):
		Pc45Demo.clear_screen()

		Pc45Demo.blink_cursor(frame=frame, color=self.cursor_color, x=self.cursor_x, y=self.cursor_y)

		if frame < 1000:
			self.write_lines1(frame)
		else:
			self.write_lines2(frame)

		if frame > 1100:
			rel_frame = frame-1100
			lngth = min(9, rel_frame//7)
			date = "8-15-1981"[:lngth]

			print(frame, lngth, date)
			Text(text=date, x=self.font_size, y=Constants.HEIGHT - 2*self.font_size, color=self.cursor_color,
			     font_size=self.font_size, anchor_x="left", anchor_y="center", font_name="Mx437 Acer710 Mono")

	def write_lines1(self, frame:int):
		if frame == 999:
			self.cursor_x = self.font_size
			self.cursor_y = Constants.HEIGHT - self.font_size

		lines1 = (("The IBM Personal Computer Basic", 100,370+17), ("Version C1.0 Copyright IBM Corp 1981", 210, 390+14*4)
		          , ("62950 Bytes free", 315, 208), ("Ok", 420, 55-12))

		self.write_lines(lines1, frame)

	def write_lines2(self, frame:int):
		lines2 = (("Current date is Tue 1-01-1980", 550, 370), ("Enter new date", 650, 200))
		self.write_lines(lines2, frame)

	def write_lines(self, lines:tuple, frame):
		for i, line in enumerate(lines):
			if frame > line[1]:
				t = Text(text=line[0], x=self.font_size, y=Constants.HEIGHT - self.font_size * (i + 1), color=self.cursor_color,
				         font_size=self.font_size, anchor_x="left", anchor_y="center", font_name="Mx437 Acer710 Mono")

				t.draw()

				self.cursor_x = line[2]
				self.cursor_y = Constants.HEIGHT - (1 + i) * self.font_size
