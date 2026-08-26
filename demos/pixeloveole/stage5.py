import arcade
import sys
import os

from datetime import datetime

from arcade import Rect
from arcade.color import CYAN, ORANGE, WHITE, YELLOW, GREEN, ARCADE_YELLOW, AQUA, BLACK

from lib.common import Globals
from lib.tunnel import TunnelEffect


class Stage5:

	START_TIMER = 700

	def __init__(self):
		self.c64 = arcade.load_texture("res/computers/c64.png")
		self.atari = arcade.load_texture("res/computers/atari.png")
		self.a500 = arcade.load_texture("res/computers/a500.png")
		self.amstrad = arcade.load_texture("res/computers/amstrad.png")
		self.nes = arcade.load_texture("res/computers/nes.png")
		self.sega = arcade.load_texture("res/computers/segaMega.png")
		self.playstation = arcade.load_texture("res/computers/gejstejszyn.png")
		arcade.set_background_color(arcade.color.BLACK)
		self.effect = TunnelEffect(9, screen_width=Globals.WIDTH, screen_height=Globals.HEIGHT, color=WHITE)

	def on_draw(self, timer):
		self.effect.draw()
		self.effect.update()
		self.display_text(timer)

	def display_text(self, timer):
		t = timer - Stage5.START_TIMER
		duration = 11
		#print(t)
		x = 0.5 * Globals.WIDTH
		y = Globals.HEIGHT - 112

		if 2 < t < 2 + duration:
			arcade.draw_text("Commodore 64", x, y, color=CYAN, font_size=60, anchor_x="center")
			self.draw_pic(self.c64)

		elif 2 + duration + 2 < t < 2 + 2*duration + 2:
			arcade.draw_text("Atari 800XL", x, y, color=ORANGE, font_size=60, anchor_x="center")
			self.draw_pic(self.atari)

		elif 2 + 2*duration + 4 < t < 2 + 3*duration + 2:
			arcade.draw_text("Amiga 500", x, y, color=WHITE, font_size=60, anchor_x="center")
			self.draw_pic(self.a500)

		elif 2 + 3*duration + 4 < t < 2 + 4*duration + 2:
			arcade.draw_text("Amstrad", x, y, color=YELLOW, font_size=60, anchor_x="center")
			self.draw_pic(self.amstrad)

		elif 2 + 4*duration + 4 < t < 2 + 5*duration + 2:
			arcade.draw_text("NES", x, y, color=GREEN, font_size=60, anchor_x="center")
			self.draw_pic(self.nes)

		elif 2 + 5*duration + 4 < t < 2 + 6*duration + 2:
			arcade.draw_text("Playstation", x, y, color=AQUA, font_size=60, anchor_x="center")
			self.draw_pic(self.playstation)

		elif 2 + 6*duration + 4 < t < 2 + 7*duration + 2:
			arcade.draw_text("Sega Mega Drive", x, y, color=ARCADE_YELLOW, font_size=60, anchor_x="center")
			self.draw_pic(self.sega)

		elif 2 + 9*duration + 2 < t < 12.5 * duration:
			arcade.draw_text("Pixelove OLE", x, y-10, color=BLACK, font_size=77, anchor_x="center")
			arcade.draw_text("26.09.2026", x, Globals.HEIGHT - 202, color=BLACK, font_size=99
			                 , anchor_x="center")
			arcade.draw_text("Biblioteka Miejska w Oleśnicy", x, Globals.HEIGHT // 2.5, color=BLACK
			                 , font_size=64,anchor_x="center")

		elif t > 13*duration:
			dur = datetime.now() - Globals.start
			print("Invitro duration: " + str(dur))

			#sys.exit(0)
			print("Restarting...")
			python = sys.executable
			os.execl(python, python, *sys.argv)

		if t > 5*duration:
			cred_kd = arcade.Text(text="Music: TECT", x=0.02 * Globals.WIDTH, y=Globals.HEIGHT - 36, color=BLACK, font_size=15, anchor_x="left")
			cred_kd.draw()
			cred_tect = arcade.Text(text="Code: KD", x=0.02 * Globals.WIDTH, y=Globals.HEIGHT - 20, color=BLACK, font_size=15, anchor_x="left")
			cred_tect.draw()

	def draw_pic(self, pic):
		rect = Rect(
			x=Globals.WIDTH // 2,
			y=Globals.HEIGHT // 2,
			width=pic.width,
			height=pic.height,
			left=Globals.WIDTH // 2,
			top=Globals.HEIGHT // 2,
			right=Globals.WIDTH // 2,
			bottom=Globals.HEIGHT // 2
		)
		arcade.draw_texture_rect(
			rect=rect,
			texture=pic,
			angle=0.0,
			color=WHITE,
			alpha=255,
			pixelated=False
		)
