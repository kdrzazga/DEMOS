import arcade
from arcade import Text

from demos.pc45 import Constants
from demos.pc45.old.base import Pc45Demo
from lib.beeptyper import Typer


class Intro(Pc45Demo):
	"""IBM PC-DOS 1.00 boot screen on a green MDA monitor."""

	FONT_FILE = "Mx437_IBM_MDA.ttf"
	FONT_FAMILY = "Mx437 IBM MDA"          # internal family name embedded in the .ttf

	# MDA phosphor green sampled from the glyph cores in dos1boot.jpg
	# (avg ~ (64,225,136); brightest ~ (87,255,163) = #57FFA3). Pure arcade
	# GREEN (0,255,0) reads too harsh and misses the minty phosphor cast.
	MDA_GREEN = (87, 255, 163)

	FPS = 60                               # arcade's default update rate (frames per second)

	# The screen sits with just a blinking cursor for the first 15 s (fan / disk
	# spin-up on the soundtrack), then the DOS boot begins.
	BLINK_START = 1 * FPS                  # cursor starts blinking at 1 s
	BOOT_START = 15 * FPS                  # DOS boot sequence begins at 15 s

	# --- DOS boot timeline, in frames measured FROM BOOT_START - tweak to taste ---
	D_DATE_PROMPT = 0                      # "Enter today's date ..." printed (at 15 s)
	D_DATE_TYPE = 70                       # the operator starts typing the date
	DATE_CPS = 16                          # frames per typed character
	D_BANNER1 = 340                        # "The IBM Personal Computer DOS"
	D_BANNER2 = 380                        # "Version 1.00 ..."
	D_PROMPT_A = 470                       # "A>" command prompt appears

	DATE_PROMPT = "Enter today's date (m-d-y): "
	DATE_VALUE = "8-12-81"                 # IBM PC (5150) announced 12 Aug 1981
	BANNER1 = "The IBM Personal Computer DOS"
	BANNER2 = "Version 1.00 (C)Copyright IBM Corp 1981"

	def __init__(self):
		super().__init__()
		self.font_size = 16
		arcade.load_font("lib/resources/" + self.FONT_FILE)
		# kept for a future keystroke-beep typing effect; not driven yet
		self.beep_typer = Typer(0, Constants.HEIGHT - self.font_size,
		                        self.FONT_FILE, self.FONT_FAMILY,
		                        self.font_size, self.MDA_GREEN)
		self.cursor_color = self.MDA_GREEN
		self.margin_x = self.font_size
		self.line_h = int(self.font_size * 1.7)
		self.top_y = Constants.HEIGHT - self.font_size * 2

	def on_update(self, frame):
		pass

	def _row_y(self, row):
		return self.top_y - row * self.line_h

	@staticmethod
	def _blink(frame, period=60):
		return (frame % period) >= (period // 2)

	def _draw(self, text, row):
		Text(text, x=self.margin_x, y=self._row_y(row), color=self.cursor_color,
		     font_size=self.font_size, font_name=self.FONT_FAMILY,
		     anchor_x="left", anchor_y="top").draw()

	def on_draw(self, frame: int):
		Pc45Demo.clear_screen()

		# Phase 1 (1 s .. 15 s): a blank screen with just a blinking cursor at home.
		if frame < self.BOOT_START:
			if frame >= self.BLINK_START and self._blink(frame):
				self._draw("_", 0)
			return

		# Phase 2 (from 15 s): the PC-DOS 1.00 boot sequence.
		b = frame - self.BOOT_START

		# Row 0: the date prompt, then the operator types the date, with a cursor.
		if b >= self.D_DATE_PROMPT:
			line = self.DATE_PROMPT
			if b >= self.D_DATE_TYPE:
				n = min(len(self.DATE_VALUE), (b - self.D_DATE_TYPE) // self.DATE_CPS)
				line += self.DATE_VALUE[:n]
			if b < self.D_BANNER1 and self._blink(frame):
				line += "_"
			self._draw(line, 0)

		# Rows 2-3: the DOS copyright banner (printed by the system).
		if b >= self.D_BANNER1:
			self._draw(self.BANNER1, 2)
		if b >= self.D_BANNER2:
			self._draw(self.BANNER2, 3)

		# Row 5: the A> command prompt with a blinking underscore cursor.
		if b >= self.D_PROMPT_A:
			self._draw("A>" + ("_" if self._blink(frame) else ""), 5)
