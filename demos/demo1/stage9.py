import arcade
from arcade import Sprite
from arcade.color import BLACK

from demos.demo1 import Constants
from demos.demo1.stage8unshaved1 import Stage8
from demos.demo1.talking_heads import TalkingHead


class Stage9(Stage8):
	START_FRAME = Stage8.START_FRAME + 700

	def __init__(self):
		super().__init__()
		unshaved2 = TalkingHeadEars(Constants.RES_PATH + "talking-heads/unshaved2.png")
		self.head = unshaved2
		self.left = 0.8*Constants.WIDTH
		self.start_frame = Stage9.START_FRAME
		self.bubble = self.create_bubble("bubble1.png", Constants.WIDTH // 4)

		self.speech = arcade.load_sound(Constants.RES_PATH + "talking-heads/speech2.wav")
		self.speech_end_frame = 830

	def on_draw(self, frame):
		super().clear_screen(BLACK)
		relative_frame = frame - Stage9.START_FRAME
		self.head.draw(0.56*Constants.WIDTH)

		if relative_frame < self.speech_end_frame:
			arcade.draw_sprite(self.bubble)
		if relative_frame == 1:
			print("8 BIT COMMODORE MACHINES WERE POPULARLY KNOWN IN POLAND BY THE AFFECTIONATE NAME OF “KOMODA”,"
			      "A WORD ALSO USED TO DESIGNATE A CERTAIN PIECE OF FURNITURE WHICH EVENTUALLY BECAME THE "
			      "FIRST HALF OF THE MAGAZINE NAME.")
			self.speech.play(loop=False)
		#print(relative_frame)


class TalkingHeadEars(TalkingHead):

	def __init__(self, spritesheet_path, width=288, height=333, chin_y=480):
		super().__init__(spritesheet_path, width, height, chin_y)
		spritesheet = arcade.load_texture(spritesheet_path)

		texture_ear1 = spritesheet.crop(850, 118, 90, 120)
		texture_ear2 = spritesheet.crop(959-90, 430, 90, 120)

		self.ear1 = Sprite(path_or_texture=texture_ear1)
		self.ear2 = Sprite(path_or_texture=texture_ear2)

		for ear in (self.ear1, self.ear2):
			ear.center_y = self.current_face.center_y
			ear.scale = (0.5, 0.5)

	def draw(self, x):
		super().draw(x)
		arcade.draw_sprite(self.ear1)
		arcade.draw_sprite(self.ear2)

		self.ear1.center_x = self.current_face.center_x + self.current_face.width//2 + self.ear1.width//2 - 10
		self.ear2.center_x = self.current_face.center_x - self.current_face.width//2 - self.ear2.width//2 + 10
