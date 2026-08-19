import math

from arcade import Sprite, SpriteList
from lib.common import Globals


class Stage3:

	START_TIMER = 446

	def __init__(self):
		self.move_coeff = 1

		slide1 = Sprite("res/slideshow/party (1).jpeg")
		slide2 = Sprite("res/slideshow/party (2).jpeg")
		slide3 = Sprite("res/slideshow/party (3).jpeg")
		slide4 = Sprite("res/slideshow/party (4).jpeg")
		slide5 = Sprite("res/slideshow/party (5).jpeg")
		slide6 = Sprite("res/slideshow/party (6).jpeg")

		self.slides = SpriteList()
		all_slides = (slide1, slide2, slide3, slide4, slide5, slide6)

		for slide in all_slides:
			self.slides.append(slide)

	def on_draw(self, timer):
		#print('')
		self.rotate(timer)

	def rotate(self, timer):
		angle_shift = self.move_coeff * (timer - Stage3.START_TIMER) * math.pi / 50
		# angle_shift = angle_shift % 6.28
		for i, slide in enumerate(self.slides):
			self.slides[i].scale = 0.3
			angle = angle_shift + i / len(self.slides) * math.pi * 2
			radius = 220
			x1 = Globals.WIDTH // 2 + radius * math.sin(angle)
			y1 = 5 * Globals.HEIGHT // 9 + radius * math.cos(angle) + 50
			self.slides[i].center_x = x1
			self.slides[i].center_y = y1
		self.slides.draw()
		trunc_timer = int((timer - Stage3.START_TIMER) / Globals.TIMER_INC)
		if trunc_timer % 75 == 1:
			self.slides.shuffle()
		elif trunc_timer % 300 == 2:
			self.move_coeff = -self.move_coeff
			#print(trunc_timer, end=' ')


