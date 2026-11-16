import numpy as np
import pygame


class ColorGradient:

	def __init__(self, name, top_color, bottom_color):
		self.name = name
		self.top_color = top_color
		self.bottom_color = bottom_color
		self.vertical_share = 0.8

	def paint(self, area):
		width, height = area.shape
		columns, rows = np.mgrid[0:width, 0:height].astype(np.float32)
		blend_amount = (rows / max(1, height - 1) * self.vertical_share
		                + columns / max(1, width - 1) * (1.0 - self.vertical_share))[:, :, None]
		top = np.array(self.top_color, dtype=np.float32)
		bottom = np.array(self.bottom_color, dtype=np.float32)
		surface = pygame.Surface((width, height), pygame.SRCALPHA)
		colors = pygame.surfarray.pixels3d(surface)
		alpha = pygame.surfarray.pixels_alpha(surface)
		colors[:] = (top * (1.0 - blend_amount) + bottom * blend_amount).astype(np.uint8)
		alpha[area] = 255
		del colors, alpha
		return surface


class GradientPalette:

	def __init__(self):
		self.gradients = [
			ColorGradient("BLUE_TO_VIOLET", (40, 140, 255), (160, 60, 230)),
			ColorGradient("YELLOW_TO_BLUE", (255, 225, 60), (50, 120, 255)),
			ColorGradient("PINK_TO_ORANGE", (255, 80, 170), (255, 170, 40)),
			ColorGradient("GREEN_TO_CYAN", (150, 235, 60), (40, 200, 220)),
		]
