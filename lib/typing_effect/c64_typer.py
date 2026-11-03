from lib.globals import Constants
from lib.typing_effect.typer import FONT_PATH, Typer


class C64Typer(Typer):

	def __init__(self, c64_frame, row, column, text, start_time):
		self.c64_frame = c64_frame
		self.row = row
		self.column = column
		self.letters_per_second = 8.0
		self.cell_width = c64_frame.cell_width
		self.cell_height = c64_frame.cell_height
		glyphs = "".join(chr(Constants.FONT_BASE + ord(character)) for character in text.upper())
		start_x = c64_frame.char_x + column * self.cell_width
		start_y = c64_frame.char_y + row * self.cell_height
		super().__init__(self.frame_at(start_time), glyphs, c64_frame.surface, start_x, start_y,
						 self.cell_height, FONT_PATH)
		self.color = Constants.PALETTE[14]

	def frame_at(self, seconds):
		return int(seconds * self.letters_per_second)

	def type_at(self, seconds, beeping=False):
		self.type(self.frame_at(seconds), beeping)

	def visible_letters(self, seconds):
		typed = self.frame_at(seconds) - self.start_frame
		return min(max(typed, 0), len(self.text))

	def is_typing(self, seconds):
		return 0 < self.visible_letters(seconds) < len(self.text)

	def is_finished(self, seconds):
		return self.visible_letters(seconds) == len(self.text)

	def cursor_position(self, seconds):
		if self.is_finished(seconds):
			return self.c64_frame.char_x, self.start_y + self.cell_height
		return self.start_x + self.visible_letters(seconds) * self.cell_width, self.start_y

	def draw_cursor(self, seconds):
		cursor_x, cursor_y = self.cursor_position(seconds)
		self.surface.fill(self.color, (cursor_x, cursor_y, self.cell_width, self.cell_height))
