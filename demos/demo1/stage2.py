import arcade
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.stage1 import Stage1
from lib.animated_sprite import AnimatedSprite
from lib.c64 import C64


class Stage2(C64):

	START_FRAME = Stage1.START_FRAME + 200

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

		#print(frame, end=' ')
		self.tramiels.update(0.16)
		self.tramiels.draw()

		if frame > Stage2.START_FRAME + 100:
			y = self.line_to_coord(24)
			text1 = self.create_cyan_text("Computer for the MASSES,", y)
			text1.draw()

		if frame > Stage2.START_FRAME + 140:
			y = self.line_to_coord(25)
			text2 = self.create_cyan_text("not for the classes", y)
			text2.draw()

	def create_cyan_text(self, text, yy):
		cyan = Color.from_hex_string(Constants.CYAN)

		return arcade.Text(text=text, x=Constants.WIDTH * 0.1, y=yy, color=cyan,
			font_size=self.font_size, font_name="C64 Pro Mono", anchor_x="left")
