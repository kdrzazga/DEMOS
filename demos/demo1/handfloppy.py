import arcade
from arcade import Sprite

from demos.demo1 import Constants


class Hand:
	SPEED = 3

	def __init__(self):
		self.arm = Sprite(Constants.RES_PATH + "hand.png", center_x=0.3*Constants.WIDTH, center_y=-230)
		self.fingers = Sprite(Constants.RES_PATH + "fingers.png", center_x=0.3*Constants.WIDTH, center_y=-230)
		self.floppy = Sprite(Constants.RES_PATH + "floppy.png", center_x=0.3*Constants.WIDTH, center_y=-230)

	def draw(self):
		arcade.draw_sprite(self.fingers)
		arcade.draw_sprite(self.floppy)
		arcade.draw_sprite(self.arm)

	def update(self):
		self.move_up()

	def move_up(self):
		self.arm.center_y += Hand.SPEED
		self.fingers.center_y += Hand.SPEED
		self.floppy.center_y += Hand.SPEED

	def move_down(self):
		self.arm.center_y -= Hand.SPEED
		self.fingers.center_y -= Hand.SPEED
