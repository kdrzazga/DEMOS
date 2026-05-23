import arcade
from arcade import Sprite

from demos.demo1 import Constants
from lib.c64 import C64


class Stage2(C64):

	START_FRAME = 400

	def __init__(self):
		super().__init__()
		self.sound = arcade.load_sound("demos/demo1/resources/masses-not-classes.mp3")
		self.tramiel = Sprite("demos/demo1/resources/tramiel.png")
		self.tramiel.center_x = Constants.HEIGHT//2
		self.tramiel.center_y = 1*Constants.WIDTH//4

	def on_draw(self, frame):
		super().on_draw(frame)
		if frame == Stage2.START_FRAME + 1:
			self.sound.play(loop=False)
		print(frame, end=' ')
		arcade.draw_sprite(self.tramiel)
		self.tramiel.scale_x += 0.0015
		self.tramiel.scale_y += 0.0015
		self.tramiel.bottom +=0.7
