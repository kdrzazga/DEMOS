import pygame

from lib.urban.neon.signs import NeonSign
from lib.urban.neon.textures import SignArt


class BrandRule:

    def __init__(self, period, offset, caption, tube_color):
        self.period = period
        self.offset = offset
        self.caption = caption
        self.tube_color = tube_color

    def matches(self, sign_number):
        return sign_number % self.period == self.offset


class CaptionStyle:

    def __init__(self, caption, tube_color):
        self.caption = caption
        self.tube_color = tube_color


class VerticalCaptionPainter:

    def __init__(self):
        self.panel_width = 48
        self.letter_height = 40
        self.margin = 8
        self.background = (10, 14, 18, 255)
        self.frame_width = 3
        self.font = pygame.font.SysFont("arial", 36, bold=True)

    def paint(self, caption, tube_color):
        letters = list(caption)
        height = 2 * self.margin + len(letters) * self.letter_height
        surface = pygame.Surface((self.panel_width, height), pygame.SRCALPHA)
        surface.fill(self.background)
        pygame.draw.rect(surface, tube_color, surface.get_rect(), self.frame_width)
        for index, letter in enumerate(letters):
            if letter == " ":
                continue
            glyph = self.font.render(letter, True, tube_color)
            center = (self.panel_width / 2.0, self.margin + (index + 0.5) * self.letter_height)
            surface.blit(glyph, glyph.get_rect(center=center))
        return surface

    def store_all(self, atlas, rules):
        arts = {}
        for rule in rules:
            surface = self.paint(rule.caption, rule.tube_color)
            width, height = surface.get_size()
            arts[rule.caption] = SignArt(atlas.add(surface), rule.tube_color, width / height)
        return arts


class LineCaptionPainter:

    def __init__(self, panel_width, panel_height):
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.margin = max(6, panel_height // 8)
        self.background = (10, 14, 18, 255)
        self.frame_width = 3
        self.font = pygame.font.SysFont("arial", 96, bold=True)

    def paint(self, caption, tube_color):
        surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        surface.fill(self.background)
        pygame.draw.rect(surface, tube_color, surface.get_rect(), self.frame_width)
        text = self.font.render(caption, True, tube_color)
        text_width, text_height = text.get_size()
        scale = min((self.panel_width - 2 * self.margin) / text_width, (self.panel_height - 2 * self.margin) / text_height)
        fitted = pygame.transform.smoothscale(text, (max(1, int(text_width * scale)), max(1, int(text_height * scale))))
        surface.blit(fitted, fitted.get_rect(center=surface.get_rect().center))
        return surface


class CaptionArtShelf:

    def __init__(self):
        self.painters = {"vertical": VerticalCaptionPainter(), "block": LineCaptionPainter(256, 160),
                         "wide": LineCaptionPainter(256, 64)}
        self.tallest_block_aspect = 0.7
        self.tallest_wide_aspect = 2.6

    def store(self, atlas, styles):
        arts = {}
        for style in styles:
            if style.caption in arts:
                continue
            arts[style.caption] = {shape: self._stored(atlas, painter.paint(style.caption, style.tube_color),
                                                       style.tube_color)
                                   for shape, painter in self.painters.items()}
        return arts

    @staticmethod
    def _stored(atlas, surface, tube_color):
        width, height = surface.get_size()
        return SignArt(atlas.add(surface), tube_color, width / height)

    def shape_for(self, aspect):
        if aspect < self.tallest_block_aspect:
            return "vertical"
        if aspect < self.tallest_wide_aspect:
            return "block"
        return "wide"


class BrandedSignField:

    def __init__(self, field, rules, brand_arts, caption_cycle, caption_arts, shelf):
        self.field = field
        self.rules = rules
        self.brand_arts = brand_arts
        self.caption_cycle = caption_cycle
        self.caption_arts = caption_arts
        self.shelf = shelf
        self.face = None
        self.sign_count = 0
        self.captioned_count = 0
        self.tallest = 9.0
        self.shortest = 3.5
        self.lowest_rise = 3.0
        self.top_clearance = 0.5
        self.glow_spread = 2.2
        self.glow_strength = 0.55

    def add(self, sign):
        self.sign_count += 1
        rule = next((rule for rule in self.rules if rule.matches(self.sign_count)), None)
        branded = self._branded(sign, self.brand_arts[rule.caption]) if rule is not None else None
        self.field.add(branded if branded is not None else self._captioned(sign))

    def _captioned(self, sign):
        style = self.caption_cycle[self.captioned_count % len(self.caption_cycle)]
        self.captioned_count += 1
        bottom_left, bottom_right, _, top_left = sign.corners
        aspect = (bottom_right - bottom_left).length() / (top_left - bottom_left).length()
        sign.art = self.caption_arts[style.caption][self.shelf.shape_for(aspect)]
        return sign

    def _branded(self, sign, art):
        base = sign.corners[0]
        rise = (base - self.face.origin).dot(self.face.up)
        if rise < self.lowest_rise:
            base = base + self.face.up * (self.lowest_rise - rise)
            rise = self.lowest_rise
        height = min(self.tallest, self.face.height - rise - self.top_clearance)
        if height < self.shortest:
            return None
        tip = base + self.face.normal * (height * art.aspect)
        lift = self.face.up * height
        return NeonSign((base, tip, tip + lift, base + lift), self.face.right, art, False,
                        self.glow_spread, self.glow_strength)
