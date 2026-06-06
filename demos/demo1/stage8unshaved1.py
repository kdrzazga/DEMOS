import arcade
from arcade import Rect
from arcade.color import BLACK

from demos.demo1 import Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage7 import Stage7
from demos.demo1.talking_heads import TalkingHead


class Stage8(Demo1Base):
	START_FRAME = Stage7.START_FRAME + 800

	def __init__(self):
		super().__init__()
		self.unshaved1 = TalkingHead(Constants.RES_PATH + "talking-heads/unshaved1.png")

	def on_draw(self, frame):
		arcade.set_background_color(BLACK)
		left = bottom = 0
		width = Constants.WIDTH
		height = Constants.HEIGHT
		right = left + width
		top = bottom + height

		x = left + width // 2
		y = bottom + height // 2
		r = Rect(left, right, bottom, top, width, height, x, y)
		arcade.draw_rect_filled(r, color=BLACK)

		self.unshaved1.draw(0.1*Constants.WIDTH)

	def on_update(self, frame, klass):
		super().on_update(frame, klass)
		relative_frame = frame - Stage8.START_FRAME
		self.unshaved1.talk(relative_frame)
