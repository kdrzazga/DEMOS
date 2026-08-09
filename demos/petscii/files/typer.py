import math
import random
from array import array

import pygame

from demos.petscii.files.globals import Constants


class Typer:

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
		self._last_letters = 0  # letters shown last frame, so we beep only on new ones
		self._beeps = []  # short blips, built lazily on first beep

	def type(self, current_frame, beeping=False):
		letters = (current_frame - self.start_frame) // self.speed
		if letters <= 0:
			return
		if beeping and letters > self._last_letters and letters <= len(self.text):
			if self.text[letters - 1] != " ":  # no blip on blanks
				self.beep()
		self._last_letters = letters
		glyph = self.font.render(self.text[:letters], False, Typer.COLOR)
		self.surface.blit(glyph, (self.start_x, self.start_y))

		print(current_frame)

	def beep(self):
		"""Play a very short, high, random-pitched blip. The blips are built once
		and replayed, so typing never stalls (Sound.play() is non-blocking)."""
		if not self._beeps:
			self._beeps = self._build_beeps()
		random.choice(self._beeps).play()

	def _build_beeps(self, count=8):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return [self._tone(random.randint(900, 1600), 18) for _ in range(count)]

	def _tone(self, frequency, duration_ms):
		sample_rate, _, channels = pygame.mixer.get_init()
		sample_count = int(sample_rate * duration_ms / 1000)
		amplitude = int(32767 * 1)
		fade = max(1, sample_count // 8)        # tiny fade in/out kills the click
		samples = array("h")
		for i in range(sample_count):
			envelope = min(i, sample_count - i, fade) / fade
			value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * i / sample_rate))
			for _ in range(channels):
				samples.append(value)
		return pygame.mixer.Sound(buffer=samples.tobytes())