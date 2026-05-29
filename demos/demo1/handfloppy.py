import arcade
from arcade import Sprite

from demos.demo1 import Constants


class Hand:

	def __init__(self):
		self.arm = Sprite("demos/demo1/resources/hand1.png", center_x=0.3*Constants.WIDTH, center_y=-230)
		self.fingers = Sprite("demos/demo1/resources/hand2fingers.png", center_x=0.3*Constants.WIDTH, center_y=-230)

	def draw(self):
		arcade.draw_sprite(self.arm)
		arcade.draw_sprite(self.fingers)

	def update(self):
		self.move_up()

	def move_up(self):
		self.arm.center_y += 1
		self.fingers.center_y += 1
