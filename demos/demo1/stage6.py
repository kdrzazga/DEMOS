from demos.demo1.stage3 import Stage3
from demos.demo1.stage5 import Stage5
from lib.c64 import C64


class Stage6(C64):
	START_FRAME = Stage5.START_FRAME + 130

	def __init__(self):
		super().__init__()

	def on_draw(self, frame):
		pass
