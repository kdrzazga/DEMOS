import os

import pygame

from lib.graffitti.graffiti_canvas import GraffitiCanvas
from lib.graffitti.graffiti_glyph import GraffitiGlyph
from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes
from lib.graffitti.spray_texture import SprayOrderMap, SprayTexture

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
THANKS_SHEET_PATH = os.path.join(RESOURCES, "ty.png")
THANKS_BACKGROUND_PATH = os.path.join(RESOURCES, "exit-bkg.png")


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

    def _trimmed_glyph(self, name, area):
        left, top, right, bottom = area
        element_rect = pygame.Rect(left, top, right - left, bottom - top).clip(self.sheet.get_rect())
        element = self.sheet.subsurface(element_rect).copy()
        element_mask = pygame.mask.from_surface(element, 1)
        kept_mask = pygame.mask.Mask(element.get_size())
        for blob in element_mask.connected_components(self.minimum_blob_pixels):
            kept_mask.draw(blob, (0, 0))
        kept_alpha = pygame.surfarray.array_alpha(
            kept_mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)))
        element_alpha = pygame.surfarray.pixels_alpha(element)
        element_alpha[kept_alpha == 0] = 0
        del element_alpha
        bounds = kept_mask.get_bounding_rects()
        content_rect = bounds[0].unionall(bounds[1:]).inflate(self.trim_padding * 2, self.trim_padding * 2)
        content_rect = content_rect.clip(element.get_rect())
        sheet_position = (element_rect.left + content_rect.left, element_rect.top + content_rect.top)
        return GraffitiGlyph(name, element.subsurface(content_rect).copy(), sheet_position)


class ThanksForWatchingGraffiti:

    def __init__(self, sheet=None, canvas_pixel_width=2048):
        self.sheet = sheet or ThanksSheet()
        self.lettering_area_shares = (0.84, 0.72)
        self.element_offsets = {
            "snake": (0, 198),
            "thank": (0, 0),
            "for": (-50, 0),
            "watching": (85, 20),
            "t": (42, -190),
        }
        self.drawing_order = ("snake", "t", "thank", "for", "watching")
        self.spray_seconds = {"snake": 1.2, "t": 1.2, "thank": 1.4, "for": 1.0, "watching": 1.6}
        self.next_element_share = 0.7
        self.first_element_delay_seconds = 0.3
        self.left_to_right_sweep = (0.15, 0.85)
        self.finished_element_blink_speed = 1.5
        self.finale_pause_seconds = 0.4
        self.finale_wave_stagger_seconds = 0.15
        self.finale_quick_blink_speed = 2.5
        self.finale_quick_blink_gap_seconds = 0.1
        self.seed = 41

        placed_rects = {name: self._placed_rect(name) for name in self.drawing_order}
        all_rects = list(placed_rects.values())
        lettering_rect = all_rects[0].unionall(all_rects[1:])
        background_glyph = GraffitiGlyph("BACKGROUND", pygame.image.load(THANKS_BACKGROUND_PATH).copy(), (0, 0))
        background_width, background_height = background_glyph.size
        area_width_share, area_height_share = self.lettering_area_shares
        self.lettering_scale = min(background_width * area_width_share / lettering_rect.width,
                                   background_height * area_height_share / lettering_rect.height)
        self.canvas = GraffitiCanvas(background_width, background_height, canvas_pixel_width)
        self.background = GraffitiPiece(SprayTexture(background_glyph, self._next_seed()),
                                        Keyframes((background_width / 2, background_height / 2)))
        self.background.progress.jump(0.0, 1.0)
        background_center = (background_width / 2, background_height / 2)
        self.elements = {name: self._element_piece(name, self._canvas_center(rect, lettering_rect, background_center))
                         for name, rect in placed_rects.items()}
        self.canvas.add(self.background, *self.elements.values())
        self.finale_start_seconds = self._schedule() + self.finale_pause_seconds
        self.duration_seconds = self._schedule_finale_blinks()

    @property
    def texture(self):
        return self.canvas.texture

    @property
    def aspect_ratio(self):
        return self.canvas.aspect_ratio

    def render(self, seconds):
        self.canvas.render(seconds)

    def blink_outline(self, element_name, start_seconds, speed=1.0):
        self.elements[element_name].blink_outline(start_seconds, speed)

    def blink_all_outlines(self, start_seconds, stagger_seconds=0.0, speed=1.0):
        for index, name in enumerate(self.drawing_order):
            self.elements[name].blink_outline(start_seconds + index * stagger_seconds, speed)
        return start_seconds + (len(self.drawing_order) - 1) * stagger_seconds + self._blink_duration(speed)

    def reset_outline_blinks(self):
        for piece in self.elements.values():
            piece.outline_blink.clear()
        self._schedule_finished_element_blinks()
        self._schedule_finale_blinks()

    def _blink_duration(self, speed):
        return self.elements[self.drawing_order[0]].outline_blink.duration_seconds(speed)

    def _next_seed(self):
        self.seed += 1
        return self.seed

    def _placed_rect(self, name):
        glyph = self.sheet[name]
        offset_x, offset_y = self.element_offsets[name]
        sheet_x, sheet_y = glyph.cell_offset
        return pygame.Rect(sheet_x + offset_x, sheet_y + offset_y, *glyph.size)

    def _canvas_center(self, placed_rect, lettering_rect, background_center):
        background_center_x, background_center_y = background_center
        return (background_center_x + (placed_rect.centerx - lettering_rect.centerx) * self.lettering_scale,
                background_center_y + (placed_rect.centery - lettering_rect.centery) * self.lettering_scale)

    def _element_piece(self, name, canvas_center):
        seed = self._next_seed()
        order_map = SprayOrderMap(seed)
        order_map.row_sweep_weight, order_map.column_sweep_weight = self.left_to_right_sweep
        spray_texture = SprayTexture(self.sheet[name], seed, order_map)
        return GraffitiPiece(spray_texture, Keyframes(canvas_center), self.lettering_scale)

    def _spray_windows(self):
        start = self.first_element_delay_seconds
        windows = {}
        for name in self.drawing_order:
            duration = self.spray_seconds[name]
            windows[name] = (start, duration)
            start += duration * self.next_element_share
        return windows

    def _schedule(self):
        finish = 0.0
        for name, (start, duration) in self._spray_windows().items():
            self.elements[name].spray(start, duration)
            finish = max(finish, start + duration)
        self._schedule_finished_element_blinks()
        return finish

    def _schedule_finished_element_blinks(self):
        for name, (start, duration) in self._spray_windows().items():
            self.elements[name].blink_outline(start + duration, self.finished_element_blink_speed)

    def _schedule_finale_blinks(self):
        blink_end = self.blink_all_outlines(self.finale_start_seconds, self.finale_wave_stagger_seconds)
        return self.blink_all_outlines(blink_end + self.finale_quick_blink_gap_seconds,
                                       speed=self.finale_quick_blink_speed)
