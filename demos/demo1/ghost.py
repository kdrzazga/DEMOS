import arcade
from arcade import Sprite

from demos.demo1 import Constants


class Ghost:

	top_left = (Constants.WIDTH // 20, Constants.HEIGHT // 20)
	top_right = (19 * Constants.WIDTH // 20, Constants.HEIGHT // 20)
	bottom_left = (Constants.WIDTH // 20, 19 * Constants.HEIGHT // 20)
	bottom_right = (19 * Constants.WIDTH // 20, 19 * Constants.HEIGHT // 20)

	def __init__(self, name):
		print(Ghost.__name__ + " " + name)
		init_data = [('blinky', Ghost.top_left), ('inky', Ghost.top_right), ('pinky', Ghost.bottom_left), ('clyde', Ghost.bottom_right), ]
		path = Constants.RES_PATH + "ghosts/" + name + ".png"
		self.speed = 1
		for name1, position in init_data:
			if name == name1:
				self.sprite = Sprite(path, center_x=position[0], center_y=position[1])
				break

	def draw(self):
		if self.sprite:
			arcade.draw_sprite(self.sprite)
		else:
			print("Sprite not created for", self)
