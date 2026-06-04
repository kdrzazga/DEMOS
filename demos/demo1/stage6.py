import arcade

from demos.demo1 import Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage5 import Stage5


class Stage6(Demo1Base):

	START_FRAME = Stage5.START_FRAME + 130

	def __init__(self):
		super().__init__()
		path = Constants.RES_PATH + "shining-ka/"
		self.shining1 = arcade.load_texture(path + "ka1.png")
		self.shining2 = arcade.load_texture(path + "ka2.png")
		self.shining3 = arcade.load_texture(path + "ka3.png")
		self.shining4 = arcade.load_texture(path + "ka4.png")
		self.shining5 = arcade.load_texture(path + "ka5.png")
		self.shining6 = arcade.load_texture(path + "ka6.png")

	def on_draw(self, frame):
		relative_frame = frame - Stage6.START_FRAME
		r = self.create_bkg_rect()
		interval = 3
		last = 6 * interval

		relative_frame = relative_frame % last

		if relative_frame < interval:
			arcade.draw_texture_rect(self.shining1, rect=r)
		elif relative_frame < 2*interval:
			arcade.draw_texture_rect(self.shining2, rect=r)
		elif relative_frame < 3*interval:
			arcade.draw_texture_rect(self.shining3, rect=r)
		elif relative_frame < 4*interval:
			arcade.draw_texture_rect(self.shining4, rect=r)
		elif relative_frame < 5*interval:
			arcade.draw_texture_rect(self.shining5, rect=r)
		elif relative_frame < 6*interval:
			arcade.draw_texture_rect(self.shining6, rect=r)
