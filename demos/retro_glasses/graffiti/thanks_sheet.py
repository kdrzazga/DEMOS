import pygame

from demos.retro_glasses.graffiti.resources_paths import THANKS_SHEET_PATH
from lib.graffitti.graffiti_glyph import GraffitiGlyph


class ThanksSheet:

    def __init__(self, path=THANKS_SHEET_PATH):
        self.element_areas = {
            "snake": (0, 0, 409, 182),
            "thank": (0, 183, 328, 364),
            "for": (328, 183, 813, 364),
            "watching": (0, 364, 813, 592),
            "t": (0, 592, 745, 813),
        }
        self.grid_line_coverage = 0.95
        self.minimum_blob_pixels = 60
        self.trim_padding = 3
        self.sheet = self._load_without_grid_lines(path)
        self.glyphs = {name: self._trimmed_glyph(name, area) for name, area in self.element_areas.items()}

    def __getitem__(self, name):
        return self.glyphs[name]

    def _load_without_grid_lines(self, path):
        sheet = pygame.image.load(path).copy()
        alpha = pygame.surfarray.pixels_alpha(sheet)
        row_coverage = (alpha > 0).mean(axis=0)
        alpha[:, row_coverage > self.grid_line_coverage] = 0
        del alpha
        return sheet

    def _element_surface(self, area):
        left, top, right, bottom = area
        element_rect = pygame.Rect(left, top, right - left, bottom - top).clip(self.sheet.get_rect())
        return self.sheet.subsurface(element_rect).copy(), element_rect.topleft

    def _mask_without_specks(self, element):
        kept_mask = pygame.mask.Mask(element.get_size())
        for blob in pygame.mask.from_surface(element, 1).connected_components(self.minimum_blob_pixels):
            kept_mask.draw(blob, (0, 0))
        return kept_mask

    @staticmethod
    def _erase_outside(element, kept_mask):
        kept_alpha = pygame.surfarray.array_alpha(
            kept_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)))
        element_alpha = pygame.surfarray.pixels_alpha(element)
        element_alpha[kept_alpha == 0] = 0
        del element_alpha

    def _content_rect(self, element, kept_mask):
        bounds = kept_mask.get_bounding_rects()
        padded = bounds[0].unionall(bounds[1:]).inflate(self.trim_padding * 2, self.trim_padding * 2)
        return padded.clip(element.get_rect())

    def _trimmed_glyph(self, name, area):
        element, (element_left, element_top) = self._element_surface(area)
        kept_mask = self._mask_without_specks(element)
        self._erase_outside(element, kept_mask)
        content_rect = self._content_rect(element, kept_mask)
        sheet_position = (element_left + content_rect.left, element_top + content_rect.top)
        return GraffitiGlyph(name, element.subsurface(content_rect).copy(), sheet_position)
