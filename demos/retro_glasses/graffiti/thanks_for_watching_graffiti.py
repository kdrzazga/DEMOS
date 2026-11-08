import pygame

from demos.retro_glasses.graffiti.resources_paths import THANKS_BACKGROUND_PATH
from demos.retro_glasses.graffiti.thanks_layout import ThanksLayout
from demos.retro_glasses.graffiti.thanks_sheet import ThanksSheet
from lib.graffitti.graffiti_canvas import GraffitiCanvas
from lib.graffitti.graffiti_glyph import GraffitiGlyph
from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes
from lib.graffitti.spray_texture import SprayOrderMap, SprayTexture


class ThanksForWatchingGraffiti:

    def __init__(self, sheet=None, canvas_pixel_width=2048):
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

        background_glyph = GraffitiGlyph("BACKGROUND", self._black_rect_like(THANKS_BACKGROUND_PATH), (0, 0))
        self.layout = ThanksLayout(sheet or ThanksSheet(), background_glyph.size)
        self.canvas = GraffitiCanvas(*background_glyph.size, canvas_pixel_width)
        self.background = self._background_piece(background_glyph)
        self.elements = {name: self._element_piece(name) for name in self.drawing_order}
        self.canvas.add(self.background, *self.elements.values())
        self.spray_windows = self._spray_windows()
        self._schedule_sprays()
        self.finale_start_seconds = self.painting_end_seconds + self.finale_pause_seconds
        self.duration_seconds = self._schedule_blinks()

    @property
    def texture(self):
        return self.canvas.texture

    @property
    def aspect_ratio(self):
        return self.canvas.aspect_ratio

    @property
    def painting_end_seconds(self):
        return max(start + duration for start, duration in self.spray_windows.values())

    def render(self, seconds):
        self.canvas.render(seconds)

    def blink_outline(self, element_name, start_seconds, speed=1.0):
        self.elements[element_name].blink_outline(start_seconds, speed)

    def blink_all_outlines(self, start_seconds, stagger_seconds=0.0, speed=1.0):
        for index, name in enumerate(self.drawing_order):
            self.blink_outline(name, start_seconds + index * stagger_seconds, speed)
        return start_seconds + (len(self.drawing_order) - 1) * stagger_seconds + self._blink_duration(speed)

    def reset_outline_blinks(self):
        for piece in self.elements.values():
            piece.outline_blink.clear()
        self._schedule_blinks()

    def _blink_duration(self, speed):
        return self.elements[self.drawing_order[0]].outline_blink.duration_seconds(speed)

    def _next_seed(self):
        self.seed += 1
        return self.seed

    @staticmethod
    def _black_rect_like(image_path):
        black_rect = pygame.Surface(pygame.image.load(image_path).get_size(), pygame.SRCALPHA)
        black_rect.fill((0, 0, 0, 255))
        return black_rect

    def _background_piece(self, background_glyph):
        background = GraffitiPiece(SprayTexture(background_glyph, self._next_seed()),
                                   Keyframes(self.layout.background_center))
        background.progress.jump(0.0, 1.0)
        return background

    def _element_piece(self, name):
        seed = self._next_seed()
        order_map = SprayOrderMap(seed)
        order_map.row_sweep_weight, order_map.column_sweep_weight = self.left_to_right_sweep
        spray_texture = SprayTexture(self.layout.sheet[name], seed, order_map)
        return GraffitiPiece(spray_texture, Keyframes(self.layout.canvas_center(name)), self.layout.scale)

    def _spray_windows(self):
        start = self.first_element_delay_seconds
        windows = {}
        for name in self.drawing_order:
            duration = self.spray_seconds[name]
            windows[name] = (start, duration)
            start += duration * self.next_element_share
        return windows

    def _schedule_sprays(self):
        for name, (start, duration) in self.spray_windows.items():
            self.elements[name].spray(start, duration)

    def _schedule_blinks(self):
        for name, (start, duration) in self.spray_windows.items():
            self.blink_outline(name, start + duration, self.finished_element_blink_speed)
        wave_end = self.blink_all_outlines(self.finale_start_seconds, self.finale_wave_stagger_seconds)
        return self.blink_all_outlines(wave_end + self.finale_quick_blink_gap_seconds,
                                       speed=self.finale_quick_blink_speed)
