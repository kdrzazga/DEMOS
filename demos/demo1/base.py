from demos.demo1 import Globals
from lib.c64 import C64


class Demo1Base(C64):
	def on_update(self, frame, klass):
		if frame == klass.START_FRAME + 1:
			print("New stage", Globals.get_duration(), "[frame", str(frame) + "]")
