"""Renders the IBM PC-DOS 1.00 boot animation onto a pygame Surface.

This is the engine-agnostic content of the demo: given a frame number it paints
the green MDA boot screen onto an offscreen Surface. The GL front-end
(main.py) uploads that Surface as a texture and maps it onto a 3D quad.
"""

import os

import pygame

# resolve the font against the project root (DEMOS/) so it loads regardless of the
# current working directory or how the demo is launched
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BootScreen:

	WIDTH, HEIGHT = 1150, 700

	FONT_FILE = os.path.join(_ROOT, "lib", "resources", "Mx437_IBM_MDA.ttf")
	FONT_PX = 21                            # ~16 pt at 96 dpi (matches the 2D version)
	CAPTION_PX = 96
	TITLE_BIG_PX = 128
	TITLE_LINE_GAP = 6

	# MDA phosphor green sampled from the glyph cores in dos1boot.jpg (#57FFA3).
	MDA_GREEN = (87, 255, 163)
	BLACK = (0, 0, 0)

	# --- layout (top-down pixel coords, as pygame Surfaces use) ---
	MARGIN_X = 16
	TOP_MARGIN = 32
	LINE_H = 27                             # ~FONT_PX * 1.3

	FPS = 60                                # frames per second the caller drives us at

	# The screen sits with just a blinking cursor for the first 15 s (fan / disk
	# spin-up on the soundtrack), then the DOS boot begins.
	BLINK_START = 1 * FPS                   # cursor starts blinking at 1 s
	BOOT_START = 15 * FPS                   # DOS boot sequence begins at 15 s

	# --- DOS boot timeline, in frames measured FROM BOOT_START ---
	D_DATE_PROMPT = 0                       # "Enter today's date ..." printed (at 15 s)
	D_DATE_TYPE = 70                        # the operator starts typing the date
	DATE_CPS = 16                           # frames per typed character
	D_BANNER1 = 340                         # "The IBM Personal Computer DOS"
	D_BANNER2 = 380                         # "Version 1.00 ..."
	D_PROMPT_A = 470                        # "A>" command prompt appears

	DATE_PROMPT = "Enter today's date (m-d-y): "
	BANNER1 = "The IBM Personal Computer DOS"
	BANNER2 = "Version 1.00 (C)Copyright IBM Corp 1981"

	def __init__(self):
		# pygame.font must be initialised by the caller (pygame.init) first.
		self.font = pygame.font.Font(self.FONT_FILE, self.FONT_PX)
		self.caption_font = pygame.font.Font(self.FONT_FILE, self.CAPTION_PX)
		self.surface = pygame.Surface((self.WIDTH, self.HEIGHT))
		self.year = 81 # IBM PC (5150) announced 12 Aug 1981
		self.date_on_screen = True

	@staticmethod
	def _blink(frame, period=60):
		return (frame % period) >= (period // 2)

	def _blit(self, text, row):
		img = self.font.render(text, True, self.MDA_GREEN)
		self.surface.blit(img, (self.MARGIN_X, self.TOP_MARGIN + row * self.LINE_H))

	def render(self, frame: int) -> pygame.Surface:
		s = self.surface
		s.fill(self.BLACK)

		# Phase 1 (1 s .. 15 s): blank screen with just a blinking cursor at home.
		if frame < self.BOOT_START:
			if frame >= self.BLINK_START and self._blink(frame):
				self._blit("_", 0)
			return s

		# Phase 2 (from 15 s): the PC-DOS 1.00 boot sequence.
		relative_frame = frame - self.BOOT_START

		self.type_date(relative_frame, frame)

		# Rows 2-3: the DOS copyright banner (printed by the system).
		if relative_frame >= self.D_BANNER1:
			self._blit(self.BANNER1, 2)
		if relative_frame >= self.D_BANNER2:
			self._blit(self.BANNER2, 3)

		# Row 5: the A> command prompt with a blinking underscore cursor.
		if relative_frame >= self.D_PROMPT_A:
			self._blit("A>" + ("_" if self._blink(frame) else ""), 5)

		return s

	def type_date(self, relative_frame, frame):
		line = self.DATE_PROMPT
		if self.date_on_screen:
			if relative_frame >= self.D_DATE_TYPE:
				n = min(len(self.date()), (relative_frame - self.D_DATE_TYPE) // self.DATE_CPS)
				line += self.date()[:n]
			if relative_frame < self.D_BANNER1 and self._blink(frame):
				line += "_"
		self._blit(line, 0)

	def date(self):
		return f"8-12-{self.year:02d}"

	def date_pixel_rect(self):
		x = self.MARGIN_X + self.font.size(self.DATE_PROMPT)[0]
		w, h = self.font.size(self.date())
		return x, self.TOP_MARGIN, w, h

	def render_date_caption(self):
		return self.caption_font.render(self.date(), True, self.MDA_GREEN)

	def render_title(self):
		big = pygame.font.Font(self.FONT_FILE, self.TITLE_BIG_PX)
		small = pygame.font.Font(self.FONT_FILE, self.TITLE_BIG_PX // 4)
		line1 = big.render("45 years", True, self.MDA_GREEN)
		line2 = small.render("of IBM PC", True, self.MDA_GREEN)
		w = max(line1.get_width(), line2.get_width())
		h = line1.get_height() + self.TITLE_LINE_GAP + line2.get_height()
		surface = pygame.Surface((w, h), pygame.SRCALPHA)
		surface.blit(line1, ((w - line1.get_width()) // 2, 0))
		surface.blit(line2, ((w - line2.get_width()) // 2, line1.get_height() + self.TITLE_LINE_GAP))
		return surface
