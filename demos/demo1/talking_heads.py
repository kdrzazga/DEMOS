import arcade


class TalkingHead:

	def __init__(self, spritesheet_path, width=300, height=333, chin_y=480):
		spritesheet = arcade.load_texture(spritesheet_path)

		self.face1 = spritesheet.crop(0, 0, width, height)
		self.face2 = spritesheet.crop(width, 0, width, height)
		self.face3 = spritesheet.crop(2*width, 0, width, height)

		self.chin1 = spritesheet.crop(0, height, width, chin_y - height)
		self.chin2 = spritesheet.crop(width, height, width, chin_y - height)
		self.chin3 = spritesheet.crop(2*width, height, width, chin_y - height)