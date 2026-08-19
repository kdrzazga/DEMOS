import random
import arcade
from arcade import Rect, Sprite
from arcade.color import WHITE, CYAN, MAGENTA, YELLOW, RED, GREEN, MEDIUM_SKY_BLUE

from lib.common import Globals


class Stage4:

	START_TIMER = 600

	def __init__(self):
		self.logo = arcade.load_texture("res/1.jpg")
		arcade.load_font("res/C64_Pro_Mono-STYLE.ttf")
		self.scroll = Sprite("res/greetings scroll.png")
		self.scroll.center_y = Globals.HEIGHT - 133
		self.scroll.center_x = Globals.WIDTH * 2.1

	def on_draw(self, timer):
		y_shift = 50
		timer -= Stage4.START_TIMER

		rect = Rect(
			x=Globals.WIDTH // 2,  # center x
			y=y_shift + Globals.HEIGHT // 2,  # center y
			width=self.logo.width,
			height=self.logo.height,
			left=Globals.WIDTH // 2,  # optional, defaults to x - width/2
			right=Globals.HEIGHT // 2,  # optional, defaults to x + width/2
			bottom=0,  # optional, defaults to y - height/2
			top=0  # optional, defaults to y + height/2
		)

		tr = min(12 * timer, 255)

		arcade.draw_texture_rect(
			texture=self.logo,
			rect=rect,
			color=WHITE,
			angle=0.0,
			blend=True,
			alpha=tr,
			pixelated=False
		)

		if timer > 7:
			self.display_caption(timer, y_shift)
			arcade.draw_sprite(self.scroll)
			self.scroll.center_x -= 1
			#print("scroll [" + str(self.scroll.center_x) + ", " + str(self.scroll.center_y) + "]")

	def display_caption(self, timer, y_shift):

		arcade.draw_text("Ekipa i przyjaciele", 0.5 * Globals.WIDTH, Globals.HEIGHT - 105, color=CYAN, font_size=25
	                 , font_name="C64 Pro Mono", anchor_x="center")
		t = timer % 30
		if 0 < t < 6 or 21 < t < 25:
			text = arcade.Text(text="TECT", x=0.55 * Globals.WIDTH, y=y_shift + 505 + random.randint(0, 3)
			                   , color=CYAN, font_size=15, font_name="C64 Pro Mono", anchor_x="left")
			text.draw()

		if 3 < t < 9 or 25 < t < 29:
			text = arcade.Text(text="Michal", x=0.65 * Globals.WIDTH, y=y_shift + 505 + random.randint(0, 3)
			                   , color=RED, font_size=15, font_name="C64 Pro Mono", anchor_x="left")
			text.draw()
		if 2 < t < 8:
			text = arcade.Text(text="SMOK", x=0.33 * Globals.WIDTH, y=y_shift + 490 + random.randint(0, 3)
			                   , color=YELLOW, font_size=22, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
		if 6 < t < 8:
			text = arcade.Text(text="Mariusz", x=0.65 * Globals.WIDTH, y=y_shift + 525 + random.randint(0, 3)
			                   , color=YELLOW, font_size=13, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
		if 6 < t < 10:
			text = arcade.Text(text="Borg", x=0.5 * Globals.WIDTH, y=y_shift + 508 + random.randint(0, 3)
			                   , color=WHITE, font_size=15, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
		if 12 < t < 16:
			text = arcade.Text(text="KD", x=0.33 * Globals.WIDTH, y=y_shift + 380 + random.randint(0, 3)
			                   , color=WHITE, font_size=17, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
		if 14 < t < 21:
			text1 = arcade.Text(text="Brodaty", x=0.52 * Globals.WIDTH, y=y_shift + 386 + random.randint(0, 3)
			                   , color=MAGENTA, font_size=15, font_name="C64 Pro Mono", anchor_x="center")
			text1.draw()
			text2 = arcade.Text(text="Gracz", x=0.52 * Globals.WIDTH, y=y_shift + 368 + random.randint(0, 3)
			                   , color=MAGENTA, font_size=15, font_name="C64 Pro Mono", anchor_x="center")
			text2.draw()
		if 18 < t < 26:
			text = arcade.Text(text="MFX", x=0.435 * Globals.WIDTH, y=y_shift + 508 + random.randint(0, 3)
			                   , color=MEDIUM_SKY_BLUE, font_size=15, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
		if 10 < t < 15:
			text = arcade.Text(text="T_mex111", x=0.57 * Globals.WIDTH, y=y_shift + 441 + random.randint(0, 3)
			                   , color=GREEN, font_size=11, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
			text = arcade.Text(text="Tomek", x=0.73 * Globals.WIDTH, y=y_shift + 386 + random.randint(0, 3)
			                   , color=WHITE, font_size=15, font_name="C64 Pro Mono", anchor_x="center")
			text.draw()
