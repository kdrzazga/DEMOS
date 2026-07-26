import pygame

from demos.petscii.files.globals import Constants


class Typer:
	"""Types a line of text onto a surface one letter at a time."""

	COLOR = (255, 255, 255)

	def __init__(self, start_frame, text, surface, start_x, start_y, font_size=12):
		pygame.font.init()
		self.start_frame = start_frame

		self.text = text
		self.font_size = font_size
		self.font = pygame.font.Font(Constants.FONT_PATH, font_size)

		self.surface = surface
		self.start_x = start_x
		self.start_y = start_y
		self.speed = 1  # number of frames per one letter typed

	def type(self, current_frame):
		letters = (current_frame - self.start_frame) // self.speed
		if letters <= 0:
			return
		glyph = self.font.render(self.text[:letters], False, Typer.COLOR)
		self.surface.blit(glyph, (self.start_x, self.start_y))

		print(current_frame)
