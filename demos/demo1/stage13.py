from demos.demo1 import Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage12tunnel2 import Stage12


class Stage13(Demo1Base):
	START_FRAME = Stage12.START_FRAME + 800

	def on_update(self, frame, klass):
		if frame == Stage13.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
