from arcade.color import BLACK

from demos.demo1 import Constants
from demos.demo1.stage8unshaved1 import Stage8
from demos.demo1.talking_heads import TalkingHead


class Stage9(Stage8):
	START_FRAME = Stage8.START_FRAME + 400

	def __init__(self):
		super().__init__()
		unshaved2 = TalkingHead(Constants.RES_PATH + "talking-heads/unshaved2.png")
		self.head = unshaved2
		self.left = 0.8*Constants.WIDTH
		self.start_frame = Stage9.START_FRAME

	def on_draw(self, frame):
		super().clear_screen(BLACK)
		self.head.draw(0.56*Constants.WIDTH)
