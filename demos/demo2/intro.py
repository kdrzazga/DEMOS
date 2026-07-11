from arcade.color import WHITE

from demos.demo2 import Constants
from lib.beeptyper import Typer


class Intro:

	def __init__(self):

		font_size = 12
		font_name = "Mx437_Acer710_Mono"
		self.beep_typer = Typer(0, Constants.HEIGHT - font_size, font_name+".ttf", font_name, font_size, WHITE)

	def on_update(self, frame):
		return

	def on_draw(self, frame):
		if frame % 10 > 5:
			r = Rect()
