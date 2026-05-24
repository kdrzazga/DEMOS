from demos.demo1.stage3 import Stage3
from lib.c64 import C64


class Stage4(C64):
	START_FRAME = Stage3.START_FRAME + 130

	def __init__(self):
		super().__init__()

	def on_draw(self, frame):
		pass
