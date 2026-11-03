from lib.globals import Constants
from lib.typing_effect.typer import FONT_PATH, Typer


class C64Typer(Typer):

	def __init__(self, c64_frame, row, column, text, start_time):
		self.c64_frame = c64_frame
		self.row = row
		self.column = column
		self.start_time = start_time
		self.letters_per_second = 8.0
		self.cell_width = c64_frame.cell_width
		self.cell_height = c64_frame.cell_height
		glyphs = "".join(chr(Constants.FONT_BASE + ord(character)) for character in text.upper())
		start_x = c64_frame.char_x + column * self.cell_width
		start_y = c64_frame.char_y + row * self.cell_height
		super().__init__(self.frame_at(start_time), glyphs, c64_frame.surface, start_x, start_y,
						 self.cell_height, FONT_PATH)
		self.text_color = Constants.PALETTE[14]
		self.color = self.text_color
		self.reverse_color = False
		self.shows_cursor = True

	def frame_at(self, seconds):
		return int(seconds * self.letters_per_second)

	def set_speed(self, letters_per_second):
		self.letters_per_second = letters_per_second
		self.start_frame = self.frame_at(self.start_time)

	@property
	def finish_time(self):
		return self.start_time + len(self.text) / self.letters_per_second

	def has_started(self, seconds):
		return seconds >= self.start_time

	def type_at(self, seconds, beeping=False):
		self.apply_colors()
		self.type(self.frame_at(seconds), beeping)

	def apply_colors(self):
		if self.reverse_color:
			self.color = Constants.PALETTE[self.c64_frame.background_color]
			self.background = self.text_color
		else:
			self.color = self.text_color
			self.background = None

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
		self.surface.fill(self.text_color, (cursor_x, cursor_y, self.cell_width, self.cell_height))
