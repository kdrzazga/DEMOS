from demos.demo1 import Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage10 import Stage10


class Stage11(Demo1Base):
	START_FRAME = Stage10.START_FRAME + 400

	def on_update(self, frame, klass):
		if frame == Stage11.START_FRAME + 1:
			print(self.__class__.__name__ +  " New stage", Globals.get_duration(), "[frame", str(frame) + "]")
