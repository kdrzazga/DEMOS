from demos.demo1.handfloppy import Hand
from demos.demo1.stage3 import Stage3
from demos.demo1.stage5 import Stage5
from lib.c64 import C64


class Stage6(C64):
	START_FRAME = Stage5.START_FRAME + 130

	def __init__(self):
		super().__init__()
		self.hand = Hand()

	def on_draw(self, frame):
		self.hand.draw()

	def on_update(self, frame):
		self.hand.move_up()
