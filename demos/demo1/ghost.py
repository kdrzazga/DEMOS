import arcade
from arcade import Sprite

from demos.demo1 import Constants


class Ghost:

	bottom_left = (Constants.WIDTH // 20, Constants.HEIGHT // 20)
	bottom_right = (19 * Constants.WIDTH // 20, Constants.HEIGHT // 20)
	top_left = (Constants.WIDTH // 20, 19 * Constants.HEIGHT // 20)
	top_right = (19 * Constants.WIDTH // 20, 19 * Constants.HEIGHT // 20)

	speed_v = Constants.HEIGHT // 40
	speed_h = Constants.WIDTH // 40

	def __init__(self, name):
		print(Ghost.__name__ + " " + name)
		init_data = [('blinky', Ghost.bottom_left), ('inky', Ghost.bottom_right), ('pinky', Ghost.top_left), ('clyde', Ghost.top_right) ]
		path = Constants.RES_PATH + "ghosts/" + name + ".png"
		self.speed_x = Ghost.speed_v
		self.speed_y = 0
		self.direction = 'left'
		for name1, position in init_data:
			if name == name1:
				self.sprite = Sprite(path, center_x=position[0], center_y=position[1])
				break

	def draw(self):
		if self.sprite:
			arcade.draw_sprite(self.sprite)
		else:
			print("Sprite not created for", self)

	def move(self):

		self.check_direction()

		self.sprite.center_x += self.speed_x
		self.sprite.center_y += self.speed_y

	def check_direction(self):
		if self.sprite.center_x == Ghost.bottom_left[0]:
			if self.sprite.center_y == Ghost.bottom_left[1]:
				self.speed_x = Ghost.speed_h
				self.speed_y = 0
			elif self.sprite.center_y == Ghost.top_left[1]:
				self.speed_x = 0
				self.speed_y = -Ghost.speed_v
		if self.sprite.center_x == Ghost.bottom_right[0]:
			if self.sprite.center_y == Ghost.bottom_right[1]:
				self.speed_x = 0
				self.speed_y = Ghost.speed_v
			elif self.sprite.center_y == Ghost.top_right[1]:
				self.speed_x = -Ghost.speed_h
				self.speed_y = 0
