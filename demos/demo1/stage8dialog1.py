import arcade
from arcade import Rect, Sprite
from arcade.color import BLACK
from arcade.types import Color

from demos.demo1 import Constants, Globals, Tools
from demos.demo1.base import Demo1Base
from demos.demo1.stage7pacman import Stage7
from demos.demo1.talking_heads import TalkingHead


class Stage8(Demo1Base):
	START_FRAME = Stage7.START_FRAME + 800

	def __init__(self):
		super().__init__()
		unshaved1 = TalkingHead(Constants.RES_PATH + "talking-heads/unshaved1.png")
		self.head = unshaved1
		self.left = 0
		self.start_frame = Stage8.START_FRAME
		self.bubble = self.create_bubble("bubble1.png", 2 * Constants.WIDTH // 4)

		self.speech = arcade.load_sound(Constants.RES_PATH + "talking-heads/speech1.wav")
		self.speech_end_frame = 585

	def on_draw(self, frame):
		relative_frame = frame - Stage8.START_FRAME
		self.clear_screen(BLACK)

		self.column_name_header(relative_frame)

		self.head.draw(0.1 * Constants.WIDTH)

		if relative_frame < self.speech_end_frame:
			arcade.draw_sprite(self.bubble)
		if relative_frame == 1:
			print("KOMODA AND AMIGA + IS A PAPER MAGAZINE DEDICATED TO COMMODORE HOME COMPUTERS PRODUCED FROM 1977 TO 1994.")
			self.speech.play(loop=False)

	def column_name_header(self, relative_frame):
		c = Color.from_hex_string(Tools.change_color(relative_frame // 6))
		arcade.Text(text='"TALKING HEADS" COLUMN', x=Constants.WIDTH // 2, y=Constants.HEIGHT * 0.12,
	            color=c, font_size=self.font_size - 1, anchor_x="center",
	            font_name="C64 Pro Mono").draw()

	def on_update(self, frame, klass):
		if frame == Stage8.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
		relative_frame = frame - self.start_frame
		if relative_frame < self.speech_end_frame:
			self.head.talk(relative_frame)
		else:
			self.head.smile()

	def create_bubble(self, relative_path, x, y=0.6*Constants.HEIGHT) -> Sprite:
		bubble = Sprite(Constants.RES_PATH + "talking-heads/" + relative_path)
		bubble.scale = (0.5, 0.5)
		bubble.center_y = y
		bubble.center_x = x
		return bubble
