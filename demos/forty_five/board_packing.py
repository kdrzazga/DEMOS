from OpenGL.GL import *

from demos.forty_five.c64breadbox.breadbin import Breadbin
from demos.forty_five.c64breadbox.breadbin_merge import BreadbinMerge


class BoardPacking:

	def __init__(self, board_arrival):
		self.board_arrival = board_arrival
		self.breadbin = Breadbin(board_arrival.board.layout)
		self.breadbin.build()
		self.merge = BreadbinMerge(self.breadbin, board_drops_in=False)
		self.hold_seconds_after_packing = 2.0
		self.seconds_since_packed = 0.0
		self.started = False

	@property
	def done(self):
		return self.started and self.merge.done and self.seconds_since_packed >= self.hold_seconds_after_packing

	def begin(self):
		self.merge.restart()
		self.seconds_since_packed = 0.0
		self.started = True

	def update(self, seconds):
		if not self.started:
			return
		if self.merge.done:
			self.seconds_since_packed += seconds
		else:
			self.merge.update(seconds)

	def _draw_case_around_board(self):
		board_x, board_y, board_z = self.breadbin.board_offset
		glTranslatef(-board_x, -board_y, -board_z)
		self.breadbin.draw()

	def draw(self):
		if self.started:
			self.board_arrival.draw_in_board_frame(self._draw_case_around_board)

	def destroy(self):
		self.breadbin.destroy()
