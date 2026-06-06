import arcade
from arcade import Rect, Sprite

from demos.demo1 import Constants


class TalkingHead:

	def __init__(self, spritesheet_path, width=288, height=333, chin_y=480, ear=False):
		spritesheet = arcade.load_texture(spritesheet_path)

		texture_face1 = spritesheet.crop(0, 0, width, height)
		texture_face2 = spritesheet.crop(width, 0, width, height)
		texture_face3 = spritesheet.crop(2*width, 0, width, height)

		texture_chin1 = spritesheet.crop(0, height, width, chin_y - height)
		texture_chin2 = spritesheet.crop(width, height, width, chin_y - height)
		texture_chin3 = spritesheet.crop(2*width, height, width, chin_y - height)

		texture_chin4 = spritesheet.crop(0, 480, width, 120)
		texture_chin5 = spritesheet.crop(width, 480, width, 120)
		texture_chin6 = spritesheet.crop(2*width, 480, width, 120)

		self.face1 = Sprite(path_or_texture=texture_face1)
		self.face2 = Sprite(path_or_texture=texture_face2)
		self.face3 = Sprite(path_or_texture=texture_face3)
		self.chin1 = Sprite(path_or_texture=texture_chin1)
		self.chin2 = Sprite(path_or_texture=texture_chin2)
		self.chin3 = Sprite(path_or_texture=texture_chin3)
		self.chin4 = Sprite(path_or_texture=texture_chin4)
		self.chin5 = Sprite(path_or_texture=texture_chin5)
		self.chin6 = Sprite(path_or_texture=texture_chin6)

		scale = 0.5

		for s in (self.face1, self.face2, self.face3, self.chin1, self.chin2, self.chin3, self.chin4, self.chin5, self.chin6):
			s.scale = (scale, scale)
			s.center_y = 2*Constants.HEIGHT // 3

		self.current_face = self.face1
		self.current_chin = self.chin6

	def draw(self, x):
		self.current_face.center_x = x + self.current_face.width//2
		self.current_chin.center_x = self.current_face.center_x
		self.current_chin.center_y = self.current_face.center_y - self.current_face.height/2 - self.current_chin.height/2

		arcade.draw_sprite(self.current_face)
		arcade.draw_sprite(self.current_chin)

	def talk(self, relative_frame):
		speed = 8
		total_cycle = 3 * speed
		cycle_position = relative_frame % total_cycle

		if cycle_position == speed:
			self.current_chin = self.chin1
		elif cycle_position == 2 * speed:
			self.current_chin = self.chin4
		elif cycle_position == 0:
			self.current_chin = self.chin5
