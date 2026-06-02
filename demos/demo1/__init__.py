from datetime import datetime


class Constants:
	WIDTH = 800
	HEIGHT = 600
	LIGHT_BLUE = "6060c0"
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
