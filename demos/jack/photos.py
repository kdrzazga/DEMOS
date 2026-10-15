import os
import re

from demos.jack.overlay import Picture
from demos.jack.revived_photoLODZ import RevivedPhoto


class StagePhoto:
    def __init__(self, appear=None, disappear=None, opacity=0.85, pop_seconds=0.2, translucent_seconds=0.5,
                 clearing_seconds=1.0, exit_seconds=0.5):
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

    def strength(self, stage, time):
        elapsed = time - stage.start_time
        window_start, window_end = stage.photo_window()
        start = window_start + (window_end - window_start) * self.appear
        end = window_start + (window_end - window_start) * self.disappear
        if elapsed <= start or elapsed >= end:
            return 0.0
        shown = elapsed - start
        clearing = min(1.0, max(0.0, (shown - self.translucent_seconds) / self.clearing_seconds))
        solidity = self.opacity + (1.0 - self.opacity) * clearing
        appearing = min(1.0, shown / self.pop_seconds)
        leaving = min(1.0, (end - elapsed) / self.exit_seconds)
        return solidity * appearing * leaving

    def update(self, dt):
        pass

    def draw(self, overlay, strength):
        raise NotImplementedError


class StillPhoto(StagePhoto):
    def __init__(self, file_name, appear=None, disappear=None):
        super().__init__(appear, disappear)
        self.picture = Picture(file_name)

    def draw(self, overlay, strength):
        overlay.draw_texture(self.picture.texture.id, overlay.fit(self.picture.aspect, overlay.photo_box()), strength)


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

    def draw(self, overlay, strength):
        area = overlay.fit(self.revived.aspect(), overlay.photo_box())
        self.revived.draw(overlay.width, overlay.height, area=area, opacity=strength)
        overlay.apply()
