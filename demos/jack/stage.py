from enum import Enum

from demos.jack.photos import PhotoLayout


class MapEra(Enum):
    PRE_WAR = 1936
    WAR = 1942
    MODERN = "modern"


class Location:
    def __init__(self, label, latitude, longitude):
        self.label = label
        self.latitude = latitude
        self.longitude = longitude


class CameraBeat:
    def __init__(self, at, framing, locations=()):
        self.at = at
        self.framing = framing
        self.locations = tuple(locations)


class Stage:
    def __init__(self, clip_number, era, year_label=None, photos=(), locations=(), framing=None, beats=(),
                 sign_dwell_seconds=0.8, photo_end_share=0.95, shortest_photo_window=1.5):
        self.clip_number = clip_number
        self.era = era
        self.year_label = year_label
        self.photos = tuple(photos)
        self.locations = tuple(locations)
        self.framing = framing
        self.beats = tuple(sorted(beats, key=lambda beat: beat.at))
        self.sign_dwell_seconds = sign_dwell_seconds
        self.photo_end_share = photo_end_share
        self.shortest_photo_window = shortest_photo_window
        self.clip = None
        self.start_time = None
        self.end_time = None
        self.photo_start = 0.0
        self.beats_due = []

    def add_photos(self, photos):
        self.photos += tuple(photos)

    def share_photo_time(self):
        unplanned = [photo for photo in self.photos if not photo.is_planned()]
        share = 1.0 / max(1, len(unplanned))
        for index, photo in enumerate(unplanned):
            photo.plan(index * share, (index + 1) * share)
        for photo in self.photos:
            photo.plan(0.0, 1.0)

    def adopt_framing(self, framing):
        if self.framing is None:
            self.framing = framing

    def schedule(self, clip, start_time):
        self.clip = clip
        self.start_time = start_time
        self.end_time = start_time + clip.duration

    @property
    def duration(self):
        return self.end_time - self.start_time

    def photo_window(self):
        end = self.duration * self.photo_end_share
        return min(self.photo_start, end - self.shortest_photo_window), end

    def enter(self, scene):
        scene.narrator.play(self.clip)
        scene.globe.show_era(self.era)
        scene.year_label.show(self.year_label)
        arrival = scene.globe.frame(self.framing, self.locations)
        self.photo_start = arrival + (self.sign_dwell_seconds if self.locations else 0.0)
        self.beats_due = list(self.beats)

    def update(self, dt, time, scene):
        elapsed = time - self.start_time
        while self.beats_due and elapsed >= self.beats_due[0].at * self.duration:
            beat = self.beats_due.pop(0)
            scene.globe.frame(beat.framing, beat.locations)
        for photo in self.photos:
            if photo.strength(self, time) > 0.0:
                photo.update(dt)

    def draw_overlay(self, overlay, time):
        shown = [(photo, photo.strength(self, time)) for photo in self.photos]
        layout = PhotoLayout(overlay.photo_box())
        for photo in self.photos:
            room = photo.room_needed(self, time)
            if room > 0.0 and photo.layer > 0:
                layout.keep_clear_of(photo.area(overlay, layout.box), room)
        for photo, strength in sorted(shown, key=lambda pair: pair[0].layer):
            if strength > 0.0:
                photo.draw(overlay, strength, layout.box)

    def leave(self, scene):
        pass


class Chapter:
    def __init__(self, framing, stage_classes):
        self.framing = framing
        self.stage_classes = tuple(stage_classes)

    def build(self, album):
        stages = [stage_class() for stage_class in self.stage_classes]
        for stage in stages:
            stage.adopt_framing(self.framing)
            stage.add_photos(album.photos_for(stage.clip_number))
            stage.share_photo_time()
        return stages
