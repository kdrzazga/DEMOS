import numpy as np
import pygame

from lib.graffitti.graffiti_sheet import GraffitiGlyph


def mask_from_array(array):
	surface = pygame.Surface(array.shape, pygame.SRCALPHA)
	alpha = pygame.surfarray.pixels_alpha(surface)
	alpha[array] = 255
	del alpha
	return pygame.mask.from_surface(surface, 1)


def array_from_mask(mask):
	surface = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
	return pygame.surfarray.array_alpha(surface) > 0


class EyesSheet:

	def __init__(self):
		self.sheet = GraffitiGlyph.from_resource("EYES", "eyes.png").surface
		self.minimum_blob_pixels = 500
		blobs = pygame.mask.from_surface(self.sheet, 1).connected_components(self.minimum_blob_pixels)
		eye_rects = sorted((blob.get_bounding_rects()[0] for blob in blobs), key=lambda rect: rect.left)
		self.left_eye, self.right_eye = (self.sheet.subsurface(rect).copy() for rect in eye_rects)


class EyePainter:

	def __init__(self, eye_surface, left_color, right_color):
		self.eye_surface = eye_surface
		self.width, self.height = eye_surface.get_size()
		self.cell_offset = (0, 0)
		self.left_color = left_color
		self.right_color = right_color
		self.outline_brightness_limit = 128
		self.hole_width_fraction = 0.36
		self.hole_height_fraction = 0.5
		self.hole_outline_width = 6
		self.pupil_radius = int(min(self.width, self.height) * 0.15)
		self.pupil_travel_fraction = 0.5
		colors = pygame.surfarray.array3d(eye_surface)
		painted = pygame.surfarray.array_alpha(eye_surface) > 0
		dark = colors.max(axis=2) < self.outline_brightness_limit
		self.outline_area = painted & dark
		self.interior_area = painted & ~dark
		self.hole_area = self._shrunken_interior(self.hole_width_fraction, self.hole_height_fraction, 0)
		self.hole_rim_area = self._shrunken_interior(self.hole_width_fraction, self.hole_height_fraction,
		                                             self.hole_outline_width)

	@property
	def pupil_travel(self):
		return ((self.width / 2 - self.pupil_radius) * self.pupil_travel_fraction,
		        (self.height / 2 - self.pupil_radius) * self.pupil_travel_fraction)

	def _shrunken_interior(self, width_fraction, height_fraction, extra_pixels):
		interior_mask = mask_from_array(self.interior_area)
		interior_rects = interior_mask.get_bounding_rects()
		interior_rect = interior_rects[0].unionall(interior_rects[1:])
		cropped_mask = pygame.mask.Mask(interior_rect.size)
		cropped_mask.draw(interior_mask, (-interior_rect.x, -interior_rect.y))
		scaled_width = int(interior_rect.width * width_fraction) + 2 * extra_pixels
		scaled_height = int(interior_rect.height * height_fraction) + 2 * extra_pixels
		scaled_mask = cropped_mask.scale((scaled_width, scaled_height))
		placed_mask = pygame.mask.Mask((self.width, self.height))
		placed_mask.draw(scaled_mask, (interior_rect.centerx - scaled_width // 2,
		                               interior_rect.centery - scaled_height // 2))
		return array_from_mask(placed_mask) & self.interior_area

	def _surface_from_areas(self, colored_areas):
		surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
		colors = pygame.surfarray.pixels3d(surface)
		alpha = pygame.surfarray.pixels_alpha(surface)
		for area, area_colors in colored_areas:
			colors[area] = area_colors[area] if isinstance(area_colors, np.ndarray) else area_colors
			alpha[area] = 255
		del colors, alpha
		return surface

	def _gradient(self):
		columns, rows = np.mgrid[0:self.width, 0:self.height].astype(np.float32)
		blend_amount = (columns / self.width * 0.6 + rows / self.height * 0.4)[:, :, None]
		left = np.array(self.left_color, dtype=np.float32)
		right = np.array(self.right_color, dtype=np.float32)
		return (left * (1.0 - blend_amount) + right * blend_amount).astype(np.uint8)

	def paint_outline(self):
		return GraffitiGlyph("O", self._surface_from_areas([(self.outline_area, (0, 0, 0))]), self.cell_offset)

	def paint_sclera(self):
		return GraffitiGlyph("SCLERA", self._surface_from_areas([(self.interior_area, (246, 244, 236))]),
		                     self.cell_offset)

	def paint_letter_fill(self):
		band_area = self.interior_area & ~self.hole_rim_area
		rim_area = self.hole_rim_area & ~self.hole_area
		return GraffitiGlyph("O_FILL", self._surface_from_areas([(band_area, self._gradient()), (rim_area, (0, 0, 0))]),
		                     self.cell_offset)

	def paint_pupil(self):
		size = self.pupil_radius * 2 + 4
		surface = pygame.Surface((size, size), pygame.SRCALPHA)
		center = (size // 2, size // 2)
		pygame.draw.circle(surface, (12, 8, 20, 255), center, self.pupil_radius)
		highlight_radius = max(3, self.pupil_radius // 4)
		highlight_center = (center[0] - self.pupil_radius // 3, center[1] - self.pupil_radius // 3)
		pygame.draw.circle(surface, (255, 255, 255, 255), highlight_center, highlight_radius)
		return GraffitiGlyph("PUPIL", surface, (0, 0))
