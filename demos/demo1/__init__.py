import math
from datetime import datetime


class Constants:
	WIDTH = 800
	HEIGHT = 600
	LIGHT_BLUE = "6060c0"
	BLACK = "000000"
	WHITE = "ffffff"
	RED = "ff0000"
	GREEN = "00ff00"
	CYAN = "00ffff"
	BROWN = "b97955"
	PURPLE = "c882c8"
	YELLOW = "ffff00"
	BLUE = "200080"

	RES_PATH = "demos/demo1/resources/"


class Globals:
	start_time = datetime.now()

	@classmethod
	def get_duration(cls):
		current_time = datetime.now()
		return current_time - Globals.start_time

class Tools:
	@staticmethod
	def change_color(t, amplitude=127.5, offset=127.5):
		b, g, r = Tools.change_color_rgb(t, amplitude, offset)
		return f"{r:02x}{g:02x}{b:02x}"

	@staticmethod
	def change_color_rgb(t, amplitude, offset):
		r = int(amplitude * math.sin(t) + offset)
		g = int(amplitude * math.sin(t + 2 * math.pi / 3) + offset)
		b = int(amplitude * math.sin(t + 4 * math.pi / 3) + offset)
		r = max(0, min(255, r))
		g = max(0, min(255, g))
		b = max(0, min(255, b))
		return b, g, r
