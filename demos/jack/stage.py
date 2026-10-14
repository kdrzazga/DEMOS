from enum import Enum


class MapEra(Enum):
    PRE_WAR = 1936
    WAR = 1942
    MODERN = "modern"


class Location:
    def __init__(self, label, latitude, longitude):
        self.label = label
        self.latitude = latitude
        self.longitude = longitude


class Stage:
    def __init__(self, clip_number, era, year_label=None, photos=(), locations=(), photo_span=(0.08, 0.95)):
        self.clip_number = clip_number
        self.era = era
        self.year_label = year_label
        self.photos = tuple(photos)
        self.locations = tuple(locations)
        self.photo_span = photo_span
        self.clip = None
        self.start_time = None
        self.end_time = None
        self._share_photo_time()

    def _share_photo_time(self):
        first, last = self.photo_span
        unplanned = [photo for photo in self.photos if not photo.is_planned()]
        share = (last - first) / max(1, len(unplanned))
        for index, photo in enumerate(unplanned):
            photo.plan(first + index * share, first + (index + 1) * share)
        for photo in self.photos:
            photo.plan(first, last)

    def schedule(self, clip, start_time):
        self.clip = clip
        self.start_time = start_time
        self.end_time = start_time + clip.duration

    @property
    def duration(self):
        return self.end_time - self.start_time

    def progress(self, time):
        return min(1.0, max(0.0, (time - self.start_time) / self.duration))

    def enter(self, scene):
        scene.narrator.play(self.clip)
        scene.globe.show_era(self.era)
        scene.globe.show_locations(self.locations)
        scene.year_label.show(self.year_label)

    def update(self, dt, time):
        for photo in self.photos:
            if photo.strength(self, time) > 0.0:
                photo.update(dt)

    def draw_overlay(self, overlay, time):
        for photo in self.photos:
            strength = photo.strength(self, time)
            if strength > 0.0:
                photo.draw(overlay, strength)

    def leave(self, scene):
        pass
