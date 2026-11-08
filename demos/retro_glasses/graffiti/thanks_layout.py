import pygame


class ThanksLayout:

    def __init__(self, sheet, background_size):
        self.sheet = sheet
        self.background_width, self.background_height = background_size
        self.lettering_area_shares = (0.84, 0.72)
        self.element_offsets = {
            "thank": (-32, 0),
            "snake": (-36, 181),
            "for": (-62, -5),
            "watching": (552, -225),
            "t": (509, -435),
        }
        self.placed_rects = {name: self._placed_rect(name) for name in self.element_offsets}
        placed = list(self.placed_rects.values())
        self.lettering_rect = placed[0].unionall(placed[1:])
        self.scale = self._fitting_scale()

    @property
    def background_center(self):
        return self.background_width / 2, self.background_height / 2

    def _placed_rect(self, name):
        glyph = self.sheet[name]
        offset_x, offset_y = self.element_offsets[name]
        sheet_x, sheet_y = glyph.cell_offset
        return pygame.Rect(sheet_x + offset_x, sheet_y + offset_y, *glyph.size)

    def _fitting_scale(self):
        area_width_share, area_height_share = self.lettering_area_shares
        return min(self.background_width * area_width_share / self.lettering_rect.width,
                   self.background_height * area_height_share / self.lettering_rect.height)

    def canvas_center(self, name):
        placed_rect = self.placed_rects[name]
        center_x, center_y = self.background_center
        return (center_x + (placed_rect.centerx - self.lettering_rect.centerx) * self.scale,
                center_y + (placed_rect.centery - self.lettering_rect.centery) * self.scale)
