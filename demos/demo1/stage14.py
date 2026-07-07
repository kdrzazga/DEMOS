from demos.demo1 import Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage13 import Stage13


class Stage14(Demo1Base):
	START_FRAME = Stage13.START_FRAME + 2200

	def on_update(self, frame, klass):
		if frame == Stage14.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

