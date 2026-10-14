import pygame

from lib.typer import Typer
from demos.jack.overlay import Picture, SurfaceSprite


class TitleCard:
    def __init__(self, overlay, fps, caption="Jack Tramiel 1928-2012", photo="TRAMIEL.jpg", fade_in=2.0,
                 typing_delay=0.6, letter_frames=5, hold=3.0, fade_out=1.5, font_share=0.055,
                 caption_top_share=0.84, band_opacity=0.45):
        self.fps = fps
        self.caption = caption
        self.picture = Picture(photo)
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.caption_top = int(overlay.height * caption_top_share)
        self.band_opacity = band_opacity
        font_size = int(overlay.height * font_share)
        self.caption_surface = pygame.Surface((overlay.width, int(font_size * 1.6)), pygame.SRCALPHA)
        self.typer = Typer(int((fade_in + typing_delay) * fps), caption, self.caption_surface, 0, 0, font_size)
        self.typer.speed = letter_frames
        self.typer.start_x = (overlay.width - self.typer.font.size(caption)[0]) // 2
        self.caption_sprite = SurfaceSprite()
        self.letters_shown = -1
        typing_seconds = len(caption) * letter_frames / fps
        self.duration = fade_in + typing_delay + typing_seconds + hold + fade_out

    def _letters_at(self, frame):
        return min(len(self.caption), max(0, (frame - self.typer.start_frame) // self.typer.speed))

    def update(self, time):
        frame = int(time * self.fps)
        letters = self._letters_at(frame)
        if letters != self.letters_shown:
            self.letters_shown = letters
            self.caption_surface.fill((0, 0, 0, 0))
            self.typer.type(frame, beeping=True)
            self.caption_sprite.upload(self.caption_surface)

    def brightness(self, time):
        return max(0.0, min(1.0, time / self.fade_in, (self.duration - time) / self.fade_out))

    def draw(self, overlay, time):
        light = self.brightness(time)
        overlay.draw_texture(self.picture.texture.id, overlay.cover(self.picture.aspect), 1.0, (light, light, light))
        band = (0.0, self.caption_top, overlay.width, self.caption_surface.get_height())
        overlay.draw_rectangle(band, (0.0, 0.0, 0.0), self.band_opacity * light)
        self.caption_sprite.draw(overlay, 0, self.caption_top, light)


class ExitCard:
    def __init__(self, photo="exit_screen.jpg", fade_in=2.5, hold=10.0, fade_out=2.5):
        self.picture = Picture(photo)
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.duration = fade_in + hold + fade_out

    def finished(self, seconds):
        return seconds >= self.duration

    def draw(self, overlay, seconds):
        overlay.darken(seconds / self.fade_in)
        light = max(0.0, min(1.0, seconds / self.fade_in, (self.duration - seconds) / self.fade_out))
        overlay.draw_texture(self.picture.texture.id, overlay.fit(self.picture.aspect, overlay.whole_screen()), light)
