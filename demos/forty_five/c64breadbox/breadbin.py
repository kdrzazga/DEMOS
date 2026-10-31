from OpenGL.GL import *

from demos.forty_five.c64breadbox.breadbin_base import BreadbinBase
from demos.forty_five.c64breadbox.breadbin_layout import BreadbinLayoutFactory
from demos.forty_five.c64breadbox.breadbin_top import BreadbinTop
from demos.forty_five.c64breadbox.keyboard import Keyboard


class Breadbin:

	def __init__(self, board_layout):
		self.layout = BreadbinLayoutFactory.create_breadbin(board_layout)
		self.keyboard = Keyboard()
		self.base = BreadbinBase(self.layout)
		self.top = BreadbinTop(self.layout, self.keyboard)
		self.base_offset = (0.0, 0.0, 0.0)
		self.board_assembly_offset = (0.0, 0.0, 0.0)
		self.top_offset = (0.0, 0.0, 0.0)
		self.keyboard_offset = (0.0, 0.0, 0.0)
		self.top_visible = True
		self.keyboard_visible = True

	@property
	def board_offset(self):
		return self.layout.board_offset

	def build(self):
		self.keyboard.build()
		self.base.build()
		self.top.build()

	def enter_board_frame(self):
		glTranslatef(*self.board_assembly_offset)
		glTranslatef(*self.board_offset)

	def enter_keyboard_frame(self):
		glTranslatef(*self.keyboard_offset)
		self.top.enter_keyboard_frame()

	def draw_base(self):
		glPushMatrix()
		glTranslatef(*self.base_offset)
		self.base.draw()
		glPopMatrix()

	def draw_top(self):
		glPushMatrix()
		glTranslatef(*self.top_offset)
		self.top.draw()
		glPopMatrix()

	def draw_keyboard(self):
		glPushMatrix()
		self.enter_keyboard_frame()
		self.keyboard.draw()
		glPopMatrix()

	def draw(self):
		self.draw_base()
		if self.top_visible:
			self.draw_top()
		if self.keyboard_visible:
			self.draw_keyboard()

	def destroy(self):
		self.keyboard.destroy()
		self.base.destroy()
		self.top.destroy()
