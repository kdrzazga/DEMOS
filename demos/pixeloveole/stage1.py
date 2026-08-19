import arcade
from arcade import Rect

from arcade.color import WHITE
from lib.common import Globals


class Stage1:

	def __init__(self):
		self.logo = arcade.load_texture("res/logo.png")
		background_music = arcade.load_sound("res/Pixelove Ole Track.mp3")

		self.media_player = background_music.play()
		self.media_player.loop = True
		self.active = True

	def on_draw(self, timer):

		rect = Rect(
			x=Globals.WIDTH // 2,  # center x
			y=Globals.HEIGHT // 2,  # center y
			width=self.logo.width,
			height=self.logo.height,
			left=Globals.WIDTH // 2,  # optional, defaults to x - width/2
			right=Globals.HEIGHT // 2,  # optional, defaults to x + width/2
			bottom=0,  # optional, defaults to y - height/2
			top=0  # optional, defaults to y + height/2
		)

		tr = min(2 * timer, 255)

		arcade.draw_texture_rect(
			texture=self.logo,
			rect=rect,
			color=WHITE,
			angle=0.0,
			blend=True,
			alpha=tr,
			pixelated=False
		)

		if timer > 200:
			self.cover_rectangles()

	def cover_rectangles(self):

		rect_size = 5
		# for x in range(self.)
		rect_left = Rect(
			x=Globals.WIDTH // 2,  # center x
			y=Globals.HEIGHT // 2,  # center y
			width=self.logo.width,
			height=self.logo.height,
			left=Globals.WIDTH // 2,  # optional, defaults to x - width/2
			right=Globals.HEIGHT // 2,  # optional, defaults to x + width/2
			bottom=0,  # optional, defaults to y - height/2
			top=0  # optional, defaults to y + height/2
		)
		arcade.draw_rect_filled(rect_left, arcade.color.WHITE, 0)
		# arcade.draw_rect_filled(rectRight, arcade.color.BLACK, 0)
