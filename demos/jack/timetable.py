import os
import re

import pygame


class Clip:
    def __init__(self, number, title, path):
        self.number = number
        self.title = title
        self.path = path
        self.sound = pygame.mixer.Sound(path)
        self.duration = self.sound.get_length()


class ClipLibrary:
    def __init__(self, folder, name_pattern=r"^(\d+)\.\s*(.+)\.mp3$"):
        self.folder = folder
        self.clips = {}
        for file_name in sorted(os.listdir(folder)):
            match = re.match(name_pattern, file_name, re.IGNORECASE)
            if match:
                number = int(match.group(1))
                self.clips[number] = Clip(number, match.group(2).strip(), os.path.join(folder, file_name))

    def clip(self, number):
        if number not in self.clips:
            raise KeyError(f"No narration clip number {number} in {self.folder}")
        return self.clips[number]


class Timetable:
    def __init__(self, stages, library, opening_seconds, gap_seconds=1.0):
        self.stages = tuple(stages)
        self.gap_seconds = gap_seconds
        cursor = opening_seconds
        for stage in self.stages:
            stage.schedule(library.clip(stage.clip_number), cursor)
            cursor = stage.end_time + gap_seconds
        self.end_time = cursor

    def stage_at(self, time):
        current = None
        for stage in self.stages:
            if stage.start_time > time:
                break
            current = stage
        return current
