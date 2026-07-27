import arcade
from arcade import Sprite

from demos.demo1 import Constants
from lib.animated_sprite import AnimatedSprite


class Hand:
	SPEED = 3

	def __init__(self):
		path = Constants.RES_PATH + "floppy/"
		self.arm = Sprite(path + "hand.png", center_x=0.3 * Constants.WIDTH, center_y=-230)
		self.fingers = Sprite(path + "fingers.png", center_x=0.3*Constants.WIDTH, center_y=-230)
		self.floppy = Sprite(path + "floppy.png", center_x=0.3*Constants.WIDTH, center_y=-230)

		self.shutter = AnimatedSprite(path + 'shutter.png', 0.3*Constants.WIDTH, Constants.HEIGHT - 114, 570//3, 68, 3, 5)

		self.pacman = AnimatedSprite(path + "pacmen.png", 0.3*Constants.WIDTH, -150, 382//5,64,5, 3)
		self.pacman_speed = 2

		self.current_bubble = None
		self.load_bubbles()

	def load_bubbles(self):
		dialogs = arcade.load_texture(Constants.RES_PATH + "floppy/dialogs.png")
		h = dialogs.height
		self.komek1_bubble = Sprite(dialogs.crop(0, 0, 176, h))    # x 0..175
		self.komek2_bubble = Sprite(dialogs.crop(176, 0, 174, h))  # x 176..349
		self.the_best_bubble = Sprite(dialogs.crop(355, 0, 90, h))  # x 355..444
		self.buy_kna_bubble = Sprite(dialogs.crop(451, 0, 90, h))   # x 451..540

		self.bubbles = (self.komek1_bubble, self.komek2_bubble, self.the_best_bubble, self.buy_kna_bubble)
		for bubble in self.bubbles:
			bubble.scale = (0.65, 0.65)
			bubble.center_y = self.pacman.sprite.center_y + self.pacman.sprite.height + 3

	def draw(self, frame):
		self.pacman.draw()
		arcade.draw_sprite(self.fingers)
		arcade.draw_sprite(self.floppy)
		arcade.draw_sprite(self.arm)

		if self.current_bubble is not None:
			arcade.draw_sprite(self.current_bubble)

		if frame > 250:
			self.shutter.draw()

	def update(self, relative_frame):
		#print(relative_frame)
		if relative_frame < 230:
			return

		if self.pacman.sprite.center_x > Constants.WIDTH * 0.85:
			self.pacman_speed = -2
		elif self.pacman.sprite.center_x < Constants.WIDTH * 0.25:
			self.pacman_speed = 2

		self.pacman.sprite.center_x += self.pacman_speed
		self.pacman.update(0.16)

		self.update_bubble(relative_frame)

		if relative_frame > 250:
			self.shutter.update(0.16)

	def update_bubble(self, relative_frame):
		if 320 <= relative_frame < 380:
			self.current_bubble = self.buy_kna_bubble
		elif 400 <= relative_frame < 470:
			self.current_bubble = self.komek1_bubble
		elif 470 <= relative_frame < 540:
			self.current_bubble = self.komek2_bubble
		elif 540 <= relative_frame < 580 or relative_frame > 765:
			self.current_bubble = self.the_best_bubble
		else:
			self.current_bubble = None

		if self.current_bubble is not None:# and relative_frame % 5 == 0:
			self.current_bubble.center_x = self.pacman.sprite.center_x
			print(self.current_bubble.center_x , ", " , self.current_bubble.center_y)



	def move_up(self):
		self.arm.center_y += Hand.SPEED
		self.fingers.center_y += Hand.SPEED
		self.floppy.center_y += Hand.SPEED
		self.pacman.sprite.center_y += Hand.SPEED
		for bubble in self.bubbles:
			bubble.center_y += Hand.SPEED

	def move_down(self):
		self.arm.center_y -= Hand.SPEED
		self.fingers.center_y -= Hand.SPEED
