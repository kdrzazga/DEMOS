import arcade
from arcade import Rect
from arcade.color import BLACK
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage2 import Stage2


class Stage3(Demo1Base):

	START_FRAME = Stage2.START_FRAME + 200

	def __init__(self):
		super().__init__()
		self.background = arcade.load_texture(Constants.RES_PATH + "kna/K&Awhite.png")

		self.text = arcade.Text(text="PROUDLY PRESENTS", x=-100, y=Constants.HEIGHT//2, color=BLACK,
			font_size=self.font_size, font_name="C64 Pro Mono", anchor_x="left")
		arcade.set_background_color(arcade.color.WHITE)

	def on_draw(self, frame):
		self.clear_background()
		self.text.draw()
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, Constants.WIDTH//2, Constants.HEIGHT//2)
		arcade.draw_texture_rect(texture=self.background, rect=r)
		self.text.x += 5

	def clear_background(self):
		wh = Color.from_hex_string(Constants.WHITE)
		r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, Constants.WIDTH // 2,
		         Constants.HEIGHT // 2)
		arcade.draw_rect_filled(r, color=wh)
