import arcade
from arcade.color import BLACK

from demos.demo1 import Globals, Constants
from demos.demo1.stage8unshaved1 import Stage8
from demos.demo1.stage9 import Stage9
from demos.demo1.talking_heads import TalkingHead


class Stage10(Stage8):
	START_FRAME = Stage9.START_FRAME + 930

	def __init__(self):
		super().__init__()
		unshaved2 = TalkingHead(Constants.RES_PATH + "talking-heads/unshaved1.png")
		self.head = unshaved2
		self.left = 0.8*Constants.WIDTH
		self.start_frame = Stage9.START_FRAME
		self.bubble = self.create_bubble("bubble1.png",3* Constants.WIDTH // 4)

		self.speech = arcade.load_sound(Constants.RES_PATH + "talking-heads/speech3.wav")
		self.speech_end_frame = 830

	def on_update(self, frame, klass):
		if frame == Stage10.START_FRAME + 1:
			print(self.__class__.__name__, Globals.get_duration(), "[frame", str(frame) + "]")

	def on_draw(self, frame):
		super().clear_screen(BLACK)
		relative_frame = frame - Stage10.START_FRAME
		self.head.draw(0.2*Constants.WIDTH)

		if relative_frame < self.speech_end_frame:
			arcade.draw_sprite(self.bubble)
		if relative_frame == 1:
			print("THE SECOND PART, AMIGA, COMES FROM COMMODORE´S RANGE OF 16 AND 32 BIT COMPUTERS,",
			      "MANUFACTURED BETWEEN 1985 AND 2004.")
			self.speech.play(loop=False)
		print(relative_frame)