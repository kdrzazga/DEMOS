import os
import re

from demos.jack.overlay import Picture
from demos.jack.revived_photoLODZ import RevivedPhoto


class StagePhoto:
    def __init__(self, appear=None, disappear=None, opacity=0.85, pop_seconds=0.2, translucent_seconds=0.5,
                 clearing_seconds=1.0, exit_seconds=0.5, room_seconds=0.6):
        self.room_seconds = room_seconds
        self.appear = appear
        self.disappear = disappear
        self.opacity = opacity
        self.pop_seconds = pop_seconds
        self.translucent_seconds = translucent_seconds
        self.clearing_seconds = clearing_seconds
        self.exit_seconds = exit_seconds

    def is_planned(self):
        return self.appear is not None or self.disappear is not None

    def plan(self, appear, disappear):
        self.appear = appear if self.appear is None else self.appear
        self.disappear = disappear if self.disappear is None else self.disappear

    def _shown_span(self, stage):
        window_start, window_end = stage.photo_window()
        return (window_start + (window_end - window_start) * self.appear,
                window_start + (window_end - window_start) * self.disappear)

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
    def __init__(self, file_name, appear=None, disappear=None, placement=None):
        super().__init__(appear, disappear)
        self.picture = Picture(file_name)
        self.placement = placement or CenteredPlacement()

    @property
    def layer(self):
        return self.placement.layer

    def area(self, overlay, box):
        return self.placement.rectangle(overlay, self.picture.aspect, box)

    def draw(self, overlay, strength, box):
        overlay.draw_texture(self.picture.texture.id, self.area(overlay, box), strength)


class PhotoAlbum:
    def __init__(self, folder, name_pattern=r"^(\d+)\.\s*.+\.(jpe?g|png)$"):
        self.folder = folder
        self.file_names = {}
        for file_name in sorted(os.listdir(folder)):
            match = re.match(name_pattern, file_name, re.IGNORECASE)
            if match:
                self.file_names.setdefault(int(match.group(1)), []).append(file_name)

    def photos_for(self, clip_number):
        return tuple(StillPhoto(file_name) for file_name in self.file_names.get(clip_number, ()))


class LivingPhoto(StagePhoto):
    def __init__(self, appear=None, disappear=None):
        super().__init__(appear, disappear)
        self.revived = RevivedPhoto()

    def update(self, dt):
        self.revived.update(dt)

    def area(self, overlay, box):
        return overlay.fit(self.revived.aspect(), box)

    def draw(self, overlay, strength, box):
        self.revived.draw(overlay.width, overlay.height, area=self.area(overlay, box), opacity=strength)
        overlay.apply()
