import arcade
from arcade.types import Color

from demos.demo1 import Constants
from lib.animated_sprite import AnimatedSprite
from lib.c64 import C64


class Stage2(C64):

	START_FRAME = 400

	def __init__(self):
		super().__init__()
		self.sound = arcade.load_sound("demos/demo1/resources/masses-not-classes.mp3")
		x = Constants.HEIGHT//2
		y = Constants.WIDTH//4
		self.tramiels = AnimatedSprite("demos/demo1/resources/tramiels.png", x, y, 1775//5,261,5, 7)

	def on_draw(self, frame):
		super().on_draw(frame)
		if frame == Stage2.START_FRAME + 1:
			self.sound.play(loop=False)
		print(frame, end=' ')
		self.tramiels.update(0.16)
		self.tramiels.draw()

		if frame > Stage2.START_FRAME + 100:
			cyan = Color.from_hex_string(Constants.CYAN)
			yy = self.line_to_coord(24)
			yy2 = self.line_to_coord(25)
			arcade.draw_text("Computer for the MASSES,", Constants.WIDTH * 0.1, yy
			                 , color=cyan, font_size=self.font_size * 1, anchor_x="left", font_name="C64 Pro Mono")
			arcade.draw_text("not for the classes", Constants.WIDTH * 0.1, yy2
			                 , color=cyan, font_size=self.font_size * 1, anchor_x="left", font_name="C64 Pro Mono")
