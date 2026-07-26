import math
import os

import arcade

from arcade import Rect, Sprite
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage12ikplus import Stage12


class Stage13(Demo1Base):
	START_FRAME = Stage12.START_FRAME + 600

	GAP_START = 150
	GAP_END = GAP_START + 450
	GAP_END2 = GAP_END + 150
	SCROLL_START = GAP_START + 80
	PHOTO_FRAMES = 337  # frames each meet-team photo stays on screen (4 x 337 ~= 1349)

	def __init__(self):
		super().__init__()
		self.font_color = "ffffff"
		self.bg_color = "000000"
		self.t = 0
		self.scroll = Scroll()
		self.photos = self.load_photos()

	def on_update(self, frame, klass):
		relative_frame = - Stage13.START_FRAME + frame
		if relative_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
		else:
			self.t += 0.05
			self.change_color()

		if relative_frame > Stage13.SCROLL_START:
			self.scroll.move()

	def on_draw(self, frame: int):
		self.clear_screen(Color.from_hex_string(self.font_color))
		super().on_draw2(frame, color=self.font_color, bg_color=self.bg_color)

		relative_frame = frame - Stage13.START_FRAME

		if Stage13.GAP_START < relative_frame < Stage13.GAP_END:
			height = min(relative_frame-150, 150)
			self.draw_gap(height)
		elif Stage13.GAP_END < relative_frame < Stage13.GAP_END2:
			height = min(relative_frame - Stage13.GAP_END - 150, 150)
			#print(relative_frame)
			self.draw_gap(height)

		if relative_frame > Stage13.SCROLL_START:
			self.scroll.draw()

		c = Color.from_hex_string(self.font_color)
		if relative_frame < Stage13.GAP_END2:
			self.blink_cursor(frame, color=c, x=0, y=9 * 14 - 7)
		else:
			f = frame - Stage13.START_FRAME - Stage13.GAP_END2
			self.background_photo(f)
			self.draw_header(self.font_color)  # re-type the C64 header on top of the photo
			self.type(f)

	def draw_gap(self, height):
		x = 0 + self.width // 2
		y = Constants.HEIGHT // 2
		r = Rect(self.left, Constants.WIDTH, self.bottom, self.top, Constants.WIDTH, height, x, y)
		arcade.draw_rect_filled(r, color=Color.from_hex_string(self.font_color))

	def change_color(self, amplitude=127.5, offset=127.5):
		b, g, r = self.change_color_rgb(self.t, amplitude, offset)
		self.font_color = f"{r:02x}{g:02x}{b:02x}"

	def change_color_rgb(self, t, amplitude, offset):
		r = int(amplitude * math.sin(t) + offset)
		g = int(amplitude * math.sin(t + 2 * math.pi / 3) + offset)
		b = int(amplitude * math.sin(t + 4 * math.pi / 3) + offset)
		r = max(0, min(255, r))
		g = max(0, min(255, g))
		b = max(0, min(255, b))
		return b, g, r

	def type(self, frame):

		# print('f=',frame)
		initial = 0 # Stage13.GAP_END2
		shift1 = 10
		shift2 = shift1 + 20
		text_struct = (("SHORT HISTORY:", initial, 11, 2.5)
		              , ("Dec 2007", initial + 100, 14, 5)
		              , ("Dec 2007 to Feb 2013", initial + 100 + shift1, 14, 5)
		              , ("Dec 2007 to Feb 2013 - C&Afan magazine", initial + 100 + shift2, 14, 5)

		              , ("May 2010", initial + 200, 17, 5)
		              , ("May 2010 - KOMODA", initial + 200 + shift1, 17, 5)
		              , ("May 2010 - KOMODA founded by Komek", initial + 200 + shift2, 17, 5)

		              , ("Oct 1, 2014", initial + 300, 20, 5.6)
		              , ("Oct 1, 2014 - Komek & friends", initial + 300 + shift1, 20, 5.6)
		              , ("Oct 1, 2014 - Komek & friends start K&A+", initial + 300 + shift2, 20, 5.6)

		              , ("Apr 4, 2015", initial + 400, 23, 5.6)
		              , ("Apr 4, 2015 - First K&A+ issue", initial + 400 + shift1, 23, 5.6)
		              , ("Apr 4, 2015 - First K&A+ issue (Polish)", initial + 400 + shift2, 23, 5.6)

		              , ("Aug 15, 2015", initial + 500, 26, 5.6)
		              , ("Aug 15, 2015 - RIP", initial + 500 + shift1, 26, 5.6)
		              , ("Aug 15, 2015 - RIP Ramos :(", initial + 500 + shift2, 26, 5.6)

		              , ("Dec 20, 2015", initial + 600, 29, 5.6)
		              , ("Dec 20, 2015 - Game LAZIK", initial + 600 + shift1, 29, 5.6)
		              , ("Dec 20, 2015 - Game LAZIK released", initial + 600 + shift2, 29, 5.6)

		              , ("Dec 22, 2015", initial + 700, 32, 5.6)
		              , ("Dec 22, 2015 - Intro", initial + 700 + shift1, 32, 5.6)
		              , ("Dec 22, 2015 - Intro MEET THE TEAM", initial + 700 + shift2, 32, 5.6)

		              , ("Apr 25, 2016", initial + 800, 35, 5.6)
		              , ("Apr 25, 2016 - Game SLAVIA 2", initial + 800 + shift1, 35, 5.6)
		              , ("Apr 25, 2016 - Game SLAVIA 2 released", initial + 800 + shift2, 35, 5.6)

		              , ("Apr 6, 2019", initial + 900, 38, 5.6)
		              , ("Apr 6, 2019 - K&A+ party", initial + 900 + shift1, 38, 5.6)
		              , ("Apr 6, 2019 - K&A+ party ?SYNTAX ERROR", initial + 900 + shift2, 38, 5.6)
		               )

		text_struct2 = (
					("Feb 21, 2020", initial + 1000, 11, 5.6)
		              , ("Feb 21, 2020 - first GO8BG", initial + 1000 + shift1, 11, 5.6)
		              , ("Feb 21, 2020 - first GO8BG disk released", initial + 1000 + shift2, 11, 5.6)

		              , ("Jun 6, 2024", initial + 1100, 14, 5.6)
		              , ("Jun 6, 2024 - first box game published:", initial + 1100 + shift1, 14, 5.6)
		              , ("Jun 6, 2024 - first box game published: TONY", initial + 1100 + shift2, 14, 5.6)

		              , ("Feb 28, 2026", initial + 1200, 17, 5.6)
		              , ("Feb 28, 2026 - K&A+ party", initial + 1200 + shift1, 17, 5.6)
		              , ("Feb 28, 2026 - K&A+ party Pixelove Ole", initial + 1200 + shift2, 17, 5.6)
		                )

		cursor_x = 0
		cursor_y = 9*12+7

		arcade_color = Color.from_hex_string(self.font_color)

		# text_struct2 reuses the same lines (11, 14, 17) as the top of
		# text_struct, so both pages cannot be on screen at once. type_with_cursor
		# keeps redrawing every past entry each frame, so we switch which page is
		# drawn: page 1 types out first, then once page 2 is due the screen turns
		# to it and text_struct2 types out fresh -- no overlay with page 1.
		page2_start = initial + 1000  # frame of text_struct2's first entry
		if frame < page2_start:
			self.type_with_cursor(arcade_color, cursor_x, cursor_y, frame, self.font_color, text_struct)
		else:
			self.type_with_cursor(arcade_color, cursor_x, cursor_y, frame, self.font_color, text_struct2)

	def load_photos(self):
		r = self.create_bkg_rect()
		folder = Constants.RES_PATH + "meet-team/"
		names = sorted(name for name in os.listdir(folder)
		               if name.lower().endswith((".jpg", ".jpeg", ".png")))
		photos = []
		for name in names:
			photos.append(Sprite(arcade.load_texture(folder + name), center_x=r.x, center_y=r.y))
		return photos

	def background_photo(self, f):
		if not self.photos:
			return
		index = min(f // Stage13.PHOTO_FRAMES, len(self.photos) - 1)
		sprite = self.photos[index]
		sprite.alpha = self.photo_alpha(f % Stage13.PHOTO_FRAMES)
		arcade.draw_sprite(sprite)

	def photo_alpha(self, local):
		# Fade each photo in then out over its PHOTO_FRAMES window: fully
		# transparent at the start, ~70% opaque (30% transparency) at the midpoint
		# (337 // 2 = 168), then back to transparent -- a soft backdrop for the
		# captions drawn on top.
		half = Stage13.PHOTO_FRAMES // 2
		peak = 0.70  # 30% transparency == 70% opacity
		if local <= half:
			opacity = peak * local / half
		else:
			opacity = peak * (Stage13.PHOTO_FRAMES - local) / (Stage13.PHOTO_FRAMES - half)
		return int(opacity * 255)



class Scroll:

	SPEED = 10

	def __init__(self):
		scroll_pic = arcade.load_texture(Constants.RES_PATH + "scroll.png")

		word_positions = (0, 344, 438, 716, 982, 1128, 1534, 1757, 1808, 2068, 2242, 2427, 2618, 2787, 2946, 3161, 3373)
		self.words = []

		for i in range(len(word_positions) - 1):
			width = word_positions[i+1] - word_positions[i]
			word = scroll_pic.crop(word_positions[i], 0, width, scroll_pic.height)
			sprite = Sprite(word, center_x=word_positions[i] + Constants.WIDTH + word.width//2, center_y=Constants.HEIGHT // 2)
			self.words.append(sprite)

	def move(self):
		for sprite in self.words:
			sprite.center_x -= Scroll.SPEED
			sprite.center_y = Constants.HEIGHT // 2 + 20 * math.cos(sprite.center_x / 140 * math.pi)
			#print(sprite.center_x)

	def draw(self):
		for sprite in self.words:
			arcade.draw_sprite(sprite)
