import arcade
from arcade import Rect
from arcade.color import BLACK

from demos.demo1 import Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage7pacman import Stage7
from demos.demo1.talking_heads import TalkingHead


class Stage8(Demo1Base):
	START_FRAME = Stage7.START_FRAME + 800

	def __init__(self):
		super().__init__()
		unshaved1 = TalkingHead(Constants.RES_PATH + "talking-heads/unshaved1.png")
		self.head = unshaved1
		self.left = 0
		self.start_frame = Stage8.START_FRAME

	def on_draw(self, frame):
		self.clear_screen(BLACK)
		self.head.draw(0.1*Constants.WIDTH)

	def on_update(self, frame, klass):
		super().on_update(frame, klass)
		relative_frame = frame - self.start_frame
		self.head.talk(relative_frame)
