from demos.demo1 import Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage11 import Stage11


class Stage12(Demo1Base):
	START_FRAME = Stage11.START_FRAME + 400

	def on_update(self, frame, klass):
		if frame == Stage12.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
