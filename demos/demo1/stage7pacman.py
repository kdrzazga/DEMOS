import arcade
from arcade import Sprite
from arcade.color import BLACK

from demos.demo1 import Constants, Globals
from demos.demo1.base import Demo1Base
from demos.demo1.ghost import Ghost
from demos.demo1.handfloppy import Hand
from demos.demo1.stage6 import Stage6


class Stage7(Demo1Base):
	START_FRAME = Stage6.START_FRAME + 200

	def __init__(self):
		super().__init__()
		self.hand = Hand()
		self.pinky = Ghost('pinky')
		self.inky = Ghost('inky')
		self.blinky = Ghost('blinky')
		self.clyde = Ghost('clyde')

		self.bkg_color = Constants.BLUE
		self.poke53280 = self.create_poke_sprite(str(53280))
		self.poke53281 = self.create_poke_sprite(str(53281))

	def create_poke_sprite(self, cell):
		poke = Sprite(Constants.RES_PATH + cell + ".png")
		poke.center_x = Constants.WIDTH // 2
		poke.center_y = Constants.HEIGHT // 2
		poke.scale = (0.05, 0.05)
		return poke

	def on_draw(self, frame):
		relative_frame = frame - Stage7.START_FRAME

		if relative_frame >= 333 + 100:
			self.bkg_color = Constants.BLACK
			self.draw_cover(Constants.BLACK)

		if relative_frame > 444 + 100:
			self.clear_screen(BLACK)
		else:
			super().draw_background(self.bkg_color)

		self.hand.draw(relative_frame)
		if relative_frame < 444 + 100:
			self.draw_cover()

		if relative_frame > 250:
			for ghost in (self.pinky, self.inky, self.blinky, self.clyde):
				ghost.draw()

			increment = 0.004
			if 333 < relative_frame < 333 + 1/increment:
				scale_x = self.poke53281.scale_x + increment
				self.poke53281.scale = (scale_x, scale_x)
				self.poke53281.center_y += 1.5
				arcade.draw_sprite(self.poke53281)
			if 444 < relative_frame < 444 + 1/increment:
				scale_x = self.poke53280.scale_x + increment
				self.poke53280.scale = (scale_x, scale_x)
				self.poke53280.center_y -= 1.5
				arcade.draw_sprite(self.poke53280)

	def on_update(self, frame, klass):
		if frame == Stage7.START_FRAME + 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")
		relative_frame = frame - Stage7.START_FRAME
		self.hand.update(relative_frame)
		if self.hand.floppy.center_y < Constants.HEIGHT//2:
			self.hand.move_up()
		else:
			self.hand.move_down()

		for ghost in (self.pinky, self.inky, self.blinky, self.clyde):
			ghost.move()
