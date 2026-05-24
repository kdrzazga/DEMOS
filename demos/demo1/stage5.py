import math
import random
import arcade

from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.stage4 import Stage4
from lib.c64 import C64


class Stage5(C64):

	START_FRAME = Stage4.START_FRAME + 100

	def __init__(self):
		super().__init__()

	def on_draw(self, frame):
		pass
