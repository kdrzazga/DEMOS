import math
import os
import re

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

from lib.particles import Texture2D


class Picture:
    def __init__(self, path):
        self.path = path
        image = pygame.image.load(path)
        self.width, self.height = image.get_size()
        raw = pygame.image.tobytes(image, "RGBA", False)
        self.texture = Texture2D(np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 4))
        self.aspect = self.width / self.height


class StagePhoto:
    def __init__(self, appear=None, disappear=None, opacity=0.85, pop_seconds=0.2, translucent_seconds=0.5,
                 clearing_seconds=1.0, exit_seconds=0.5, room_seconds=0.6, from_second=None, until_second=None):
        self.room_seconds = room_seconds
        self.from_second = from_second
        self.until_second = until_second
        self.appear = appear
        self.disappear = disappear
        self.opacity = opacity
        self.pop_seconds = pop_seconds
        self.translucent_seconds = translucent_seconds
        self.clearing_seconds = clearing_seconds
        self.exit_seconds = exit_seconds

    def is_planned(self):
        return any(value is not None for value in (self.appear, self.disappear, self.from_second, self.until_second))

    def plan(self, appear, disappear):
        self.appear = appear if self.appear is None else self.appear
        self.disappear = disappear if self.disappear is None else self.disappear

    def _shown_span(self, stage):
        window_start, window_end = stage.photo_window()
        start = window_start + (window_end - window_start) * self.appear
        end = window_start + (window_end - window_start) * self.disappear
        return (start if self.from_second is None else self.from_second,
                end if self.until_second is None else self.until_second)

    def room_needed(self, stage, time):
        elapsed = time - stage.start_time
        start, end = self._shown_span(stage)
        if elapsed <= start - self.room_seconds or elapsed >= end:
            return 0.0
        return min(1.0, (elapsed - start + self.room_seconds) / self.room_seconds)

    def strength(self, stage, time):
        elapsed = time - stage.start_time
        start, end = self._shown_span(stage)
        if elapsed <= start or elapsed >= end:
            return 0.0
        shown = elapsed - start
        clearing = min(1.0, max(0.0, (shown - self.translucent_seconds) / self.clearing_seconds))
        solidity = self.opacity + (1.0 - self.opacity) * clearing
        appearing = min(1.0, shown / self.pop_seconds)
        leaving = min(1.0, (end - elapsed) / self.exit_seconds)
        return solidity * appearing * leaving

    @property
    def layer(self):
        return 0

    def update(self, dt):
        pass

    def area(self, overlay, box):
        raise NotImplementedError

    def draw(self, overlay, strength, box):
        raise NotImplementedError


class PhotoLayout:
    def __init__(self, box, gap=20.0):
        self.box = box
        self.gap = gap

    def keep_clear_of(self, obstacle, share):
        x, y, width, height = self.box
        limit = obstacle[0] - self.gap
        if limit < x + width:
            width -= (x + width - limit) * share
        self.box = x, y, width, height


class CenteredPlacement:
    def __init__(self, layer=0):
        self.layer = layer

    def rectangle(self, overlay, aspect, box):
        return overlay.fit(aspect, box)


class BottomRightPlacement:
    def __init__(self, margin=30, height_share=0.45, layer=1):
        self.layer = layer
        self.margin = margin
        self.height_share = height_share

    def rectangle(self, overlay, aspect, box):
        height = overlay.height * self.height_share
        width = height * aspect
        return overlay.width - self.margin - width, overlay.height - self.margin - height, width, height


class StillPhoto(StagePhoto):
    def __init__(self, path, appear=None, disappear=None, placement=None, from_second=None, until_second=None):
        super().__init__(appear, disappear, from_second=from_second, until_second=until_second)
        self.picture = Picture(path)
        self.placement = placement or CenteredPlacement()

    @property
    def layer(self):
        return self.placement.layer

    def area(self, overlay, box):
        return self.placement.rectangle(overlay, self.picture.aspect, box)

    def draw(self, overlay, strength, box):
        overlay.draw_texture(self.picture.texture.id, self.area(overlay, box), strength)


class SwayingPhoto(StillPhoto):
    def __init__(self, path, appear=None, disappear=None, placement=None, from_second=None, until_second=None,
                 sway_degrees=10.0, sway_period=6.0, field_of_view=30.0):
        super().__init__(path, appear, disappear, placement, from_second, until_second)
        self.sway_degrees = sway_degrees
        self.sway_period = sway_period
        self.field_of_view = field_of_view
        self.sway_time = 0.0

    def update(self, dt):
        self.sway_time += dt

    def draw(self, overlay, strength, box):
        x, y, width, height = self.area(overlay, box)
        distance = overlay.height / 2.0 / math.tan(math.radians(self.field_of_view) / 2.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, overlay.width / overlay.height, distance * 0.2, distance * 3.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(x + width / 2.0 - overlay.width / 2.0, overlay.height / 2.0 - y - height / 2.0, -distance)
        glRotatef(self.sway_degrees * math.sin(2.0 * math.pi * self.sway_time / self.sway_period), 0.0, 1.0, 0.0)
        glBindTexture(GL_TEXTURE_2D, self.picture.texture.id)
        glColor4f(1.0, 1.0, 1.0, strength)
        half_width, half_height = width / 2.0, height / 2.0
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-half_width, half_height, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(half_width, half_height, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(half_width, -half_height, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-half_width, -half_height, 0.0)
        glEnd()
        overlay.apply()


class PhotoAlbum:
    def __init__(self, folder, name_pattern=r"^(\d+)\.\s*.+\.(jpe?g|png)$"):
        self.folder = folder
        self.file_names = {}
        for file_name in sorted(os.listdir(folder)):
            match = re.match(name_pattern, file_name, re.IGNORECASE)
            if match:
                self.file_names.setdefault(int(match.group(1)), []).append(file_name)

    def photos_for(self, clip_number):
        return tuple(StillPhoto(os.path.join(self.folder, file_name))
                     for file_name in self.file_names.get(clip_number, ()))


class LivingPhoto(StagePhoto):
    def __init__(self, animation, appear=None, disappear=None, from_second=None, until_second=None):
        super().__init__(appear, disappear, from_second=from_second, until_second=until_second)
        self.animation = animation

    def update(self, dt):
        self.animation.update(dt)

    def area(self, overlay, box):
        return overlay.fit(self.animation.aspect(), box)

    def draw(self, overlay, strength, box):
        self.animation.draw(overlay.width, overlay.height, area=self.area(overlay, box), opacity=strength)
        overlay.apply()
