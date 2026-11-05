import os

import pygame

from lib.typing_effect.typer import Typer


class Amos:

	BG_COLOR = (0, 0, 100)
	FONT_COLOR = (30, 240, 200)
	RED = (190, 30, 4)
	YELLOW = (255, 255, 11)
	WHITE = (234, 234, 234)
	BLACK = (0, 0, 0)

	def __init__(self):
		self.code_listing = None
		self.screen = AmosScreen()
		screen_width, screen_height = self.screen.size
		self.mouse_cursor = MouseCursor(int(0.75 * screen_width), int(0.75 * screen_height), screen_width)
		self.redraw()

	@property
	def surface(self):
		return self.screen.surface

	def type_code(self, file_path: str):
		with open(file_path, encoding="utf-8") as code_file:
			lines = code_file.read().splitlines()
		self.code_listing = AmosCodeListing(lines, self.screen.surface, self.screen.editor_frame.text_area,
		                                    self.screen.font, AmosCursor())
		self.redraw()

	def is_typing(self):
		return self.code_listing is not None and not self.code_listing.is_finished()

	def update(self, seconds):
		if self.code_listing is not None:
			self.code_listing.update(seconds)
		self.mouse_cursor.update(seconds)
		self.redraw()

	def redraw(self):
		self.screen.draw(self.code_listing)
		self.screen.highlight_button_at(self.mouse_cursor.x, self.mouse_cursor.y)
		self.mouse_cursor.draw(self.screen.surface)


def resource_path(file_name):
	library_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(library_directory, "resources", file_name)


class AmosFont:

	def __init__(self):
		pygame.font.init()
		self.size = 16
		self.path = resource_path("Topaznew.ttf")
		self.font = pygame.font.Font(self.path, self.size)

	def render(self, text, color):
		return self.font.render(text, False, color)

	def blit_centered(self, surface, text, color, rect):
		image = self.render(text, color)
		surface.blit(image, image.get_rect(center=rect.center))


class Icon:

	def __init__(self, rows):
		self.rows = rows

	def flipped_vertically(self):
		return Icon(list(reversed(self.rows)))

	def flipped_horizontally(self):
		return Icon([row[::-1] for row in self.rows])

	def draw(self, surface, color, box):
		for y, row in enumerate(self.rows):
			for x, pixel in enumerate(row):
				if pixel == "#":
					surface.set_at((box.x + x, box.y + y), color)


class MenuButton:

	def __init__(self, label, rect, text_color):
		self.label = label
		self.rect = pygame.Rect(rect)
		self.text_color = text_color

	def draw(self, surface, font):
		surface.fill(Amos.RED, self.rect)
		font.blit_centered(surface, self.label, self.text_color, self.rect)

	def draw_reversed(self, surface, font):
		surface.fill(Amos.WHITE, self.rect)
		font.blit_centered(surface, self.label, Amos.RED, self.rect)

	def contains(self, x, y):
		return self.rect.collidepoint(x, y)


class TopMenu:

	def __init__(self, font):
		self.font = font
		self.area = pygame.Rect(0, 0, 640, 112)
		self.logo = pygame.image.load(resource_path("amos-logo.png"))
		self.logo_cell = pygame.Rect(5, 6, 150, 62)
		self.button_size = (88, 16)
		self.first_button_left = 160
		self.column_pitch = 96
		self.row_tops = (14, 46)
		self.labels = (("Run", "Test", "Indent", "Blocks Menu", "Search Menu"),
		               ("Run Other", "Edit Other", "Insert", "Fold/Unfold", "Line Insert"))
		self.buttons = self.create_buttons()
		self.version_bar = MenuButton("Version 1.35", (8, 78, 624, 16), Amos.YELLOW)
		self.lines = self.create_lines()

	def create_buttons(self):
		return [MenuButton(label, (self.first_button_left + column * self.column_pitch, top, *self.button_size), Amos.WHITE)
		        for top, row_labels in zip(self.row_tops, self.labels)
		        for column, label in enumerate(row_labels)]

	def button_at(self, x, y):
		return next((button for button in self.buttons if button.contains(x, y)), None)

	def create_lines(self):
		outline = [pygame.Rect(4, 4, 631, 2), pygame.Rect(4, 100, 631, 2),
		           pygame.Rect(3, 6, 2, 94), pygame.Rect(635, 6, 2, 94)]
		column_separators = [pygame.Rect(155 + column * self.column_pitch, 6, 2, 62) for column in range(5)]
		row_separators = [pygame.Rect(157, 36, 478, 2), pygame.Rect(5, 68, 630, 2)]
		return outline + column_separators + row_separators

	def draw(self, surface):
		surface.fill(Amos.BLACK, self.area)
		for line in self.lines:
			surface.fill(Amos.WHITE, line)
		surface.blit(self.logo, self.logo.get_rect(center=self.logo_cell.center))
		for button in self.buttons:
			button.draw(surface, self.font)
		self.version_bar.draw(surface, self.font)


class ScrollThumb:

	def __init__(self, rect):
		self.rect = pygame.Rect(rect)

	def draw(self, surface, color):
		surface.fill(Amos.BLACK, self.rect)
		for dy in range(self.rect.height):
			for dx in range(self.rect.width):
				if dx == 0 or (dx + dy // 2) % 2 == 0:
					surface.set_at((self.rect.x + dx, self.rect.y + dy), color)


class EditorFrame:

	def __init__(self):
		self.color = Amos.FONT_COLOR
		self.text_area = pygame.Rect(0, 112, 624, 352)
		self.vertical_bar = pygame.Rect(624, 112, 16, 368)
		self.horizontal_bar = pygame.Rect(0, 464, 640, 16)
		self.tracks = [pygame.Rect(625, 130, 14, 316), pygame.Rect(17, 466, 180, 12)]
		self.horizontal_thumb = ScrollThumb((197, 466, 409, 12))
		up_arrow = Icon(["............",
		                 "............",
		                 ".....##.....",
		                 ".....##.....",
		                 "...######...",
		                 "...######...",
		                 ".....##.....",
		                 ".....##.....",
		                 ".....##.....",
		                 ".....##.....",
		                 "............",
		                 "............"])
		left_arrow = Icon(["............",
		                   "............",
		                   "..##........",
		                   "..##........",
		                   ".#########..",
		                   ".#########..",
		                   ".#########..",
		                   ".#########..",
		                   "..##........",
		                   "..##........",
		                   "............",
		                   "............"])
		ring = Icon(["............",
		             "............",
		             "............",
		             "............",
		             "....####....",
		             "....####....",
		             "..##....##..",
		             "..##....##..",
		             "....####....",
		             "....####....",
		             "............",
		             "............"])
		self.icon_boxes = [(pygame.Rect(626, 114, 12, 12), up_arrow),
		                   (pygame.Rect(626, 450, 12, 12), up_arrow.flipped_vertically()),
		                   (pygame.Rect(2, 466, 12, 12), left_arrow),
		                   (pygame.Rect(610, 466, 12, 12), left_arrow.flipped_horizontally()),
		                   (pygame.Rect(626, 466, 12, 12), ring)]

	def draw(self, surface):
		surface.fill(Amos.BG_COLOR, self.text_area)
		surface.fill(self.color, self.vertical_bar)
		surface.fill(self.color, self.horizontal_bar)
		for track in self.tracks:
			surface.fill(Amos.BLACK, track)
		self.horizontal_thumb.draw(surface, self.color)
		for box, icon in self.icon_boxes:
			surface.fill(Amos.BLACK, box)
			icon.draw(surface, self.color, box)


class AmosCursor:

	def __init__(self):
		self.color = Amos.FONT_COLOR
		self.blink_period = 0.6
		self.thickness = 2
		self.time = 0.0

	def update(self, seconds):
		self.time += seconds

	def restart_blink(self):
		self.time = 0.0

	def is_visible(self):
		return self.time % self.blink_period < self.blink_period / 2

	def draw(self, surface, cell):
		if self.is_visible():
			surface.fill(self.color, (cell.x, cell.bottom - self.thickness, cell.width, self.thickness))


class AmosTyper(Typer):

	def __init__(self, surface, area, row, text, start_letter, font):
		self.row = row
		self.letters_per_second = 75.0
		self.cell_width = 8
		self.cell_height = 16
		self.home_y = area.y + row * self.cell_height
		super().__init__(start_letter, text, surface, area.x, self.home_y, font.size, font.path)
		self.color = Amos.FONT_COLOR

	def frame_at(self, seconds):
		return int(seconds * self.letters_per_second)

	def visible_letters(self, seconds):
		return min(max(self.frame_at(seconds) - self.start_frame, 0), len(self.text))

	def has_started(self, seconds):
		return self.frame_at(seconds) >= self.start_frame

	def is_finished(self, seconds):
		return self.has_started(seconds) and self.visible_letters(seconds) == len(self.text)

	def scroll_up(self, rows):
		self.start_y = self.home_y - rows * self.cell_height

	def type_at(self, seconds, beeping=False):
		self.type(self.frame_at(seconds), beeping)

	def cursor_cell(self, seconds):
		return pygame.Rect(self.start_x + self.visible_letters(seconds) * self.cell_width, self.start_y,
		                   self.cell_width, self.cell_height)


class AmosCodeListing:

	def __init__(self, lines, surface, area, font, cursor):
		self.surface = surface
		self.area = area
		self.cursor = cursor
		self.visible_rows = area.height // 16
		self.elapsed = 0.0
		self.typers = self.create_typers(lines, font)
		self.last_progress = None

	def create_typers(self, lines, font):
		typers = []
		start_letter = 0
		for row, text in enumerate(lines):
			typers.append(AmosTyper(self.surface, self.area, row, text, start_letter, font))
			start_letter += len(text) + 1
		return typers

	def active_typer(self):
		started = [typer for typer in self.typers if typer.has_started(self.elapsed)]
		return started[-1] if started else self.typers[0]

	def is_finished(self):
		return all(typer.is_finished(self.elapsed) for typer in self.typers)

	def update(self, seconds):
		self.elapsed += seconds
		self.cursor.update(seconds)
		if not self.typers:
			return
		active = self.active_typer()
		progress = (active.row, active.visible_letters(self.elapsed))
		if progress != self.last_progress:
			self.cursor.restart_blink()
			self.last_progress = progress

	def draw(self):
		if not self.typers:
			return
		active = self.active_typer()
		scrolled_rows = max(0, active.row - (self.visible_rows - 1))
		self.surface.set_clip(self.area)
		for typer in self.typers:
			typer.scroll_up(scrolled_rows)
			typer.type_at(self.elapsed)
		self.cursor.draw(self.surface, active.cursor_cell(self.elapsed))
		self.surface.set_clip(None)


class MouseCursor:

	def __init__(self, x: int, y: int, screen_width: int):
		self.image = pygame.image.load(resource_path("amiga_cursor.png"))
		self.x = x
		self.y = y
		self.target_x = x
		self.target_y = y
		self.step_seconds = (int(1500 / screen_width) + 1) / 1000.0
		self.pending_seconds = 0.0

	def move_to(self, x: int, y: int):
		self.target_x = x
		self.target_y = y

	def is_moving(self):
		return (self.x, self.y) != (self.target_x, self.target_y)

	def update(self, seconds):
		if not self.is_moving():
			self.pending_seconds = 0.0
			return
		self.pending_seconds += seconds
		while self.pending_seconds >= self.step_seconds and self.is_moving():
			self.pending_seconds -= self.step_seconds
			self.x += self.step_towards(self.x, self.target_x)
			self.y += self.step_towards(self.y, self.target_y)

	@staticmethod
	def step_towards(current, target):
		return (target > current) - (target < current)

	def draw(self, surface):
		surface.blit(self.image, (self.x, self.y))


class AmosScreen:

	def __init__(self):
		self.size = (640, 480)
		self.surface = pygame.Surface(self.size)
		self.background = pygame.Surface(self.size)
		self.font = AmosFont()
		self.top_menu = TopMenu(self.font)
		self.editor_frame = EditorFrame()
		self.top_menu.draw(self.background)
		self.editor_frame.draw(self.background)
		self.draw()

	def draw(self, code_listing=None):
		self.surface.blit(self.background, (0, 0))
		if code_listing is not None:
			code_listing.draw()

	def highlight_button_at(self, x, y):
		hovered_button = self.top_menu.button_at(x, y)
		if hovered_button is not None:
			hovered_button.draw_reversed(self.surface, self.font)
