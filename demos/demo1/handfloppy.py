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

	def draw(self, frame):
		self.pacman.draw()
		arcade.draw_sprite(self.fingers)
		arcade.draw_sprite(self.floppy)
		arcade.draw_sprite(self.arm)
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

		if relative_frame > 250:
			self.shutter.update(0.16)

	def move_up(self):
		self.arm.center_y += Hand.SPEED
		self.fingers.center_y += Hand.SPEED
		self.floppy.center_y += Hand.SPEED
		self.pacman.sprite.center_y += Hand.SPEED

	def move_down(self):
		self.arm.center_y -= Hand.SPEED
		self.fingers.center_y -= Hand.SPEED
