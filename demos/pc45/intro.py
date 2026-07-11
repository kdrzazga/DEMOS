import arcade
from arcade import Rect
from arcade.color import WHITE

from demos.pc45 import Constants
from demos.pc45.base import Pc45Demo
from lib.beeptyper import Typer


class Intro(Pc45Demo):

	def __init__(self):

		super().__init__()
		self.font_size = 12
		font_name = "Mx437_Acer710_Mono"
		self.beep_typer = Typer(0, Constants.HEIGHT - self.font_size, font_name+".ttf", font_name, self.font_size, WHITE)
		arcade.load_font("lib/resources/Mx437_Acer710_Mono.ttf")
		self.cursor_x = self.font_size
		self.cursor_y = Constants.HEIGHT - self.font_size
		self.cursor_color = arcade.color.GREEN

	def on_update(self, frame):
		return

	def on_draw(self, frame):
		Pc45Demo.clear_screen()

		Pc45Demo.blink_cursor(frame=frame, color=self.cursor_color, x=self.cursor_x, y=self.cursor_y)
