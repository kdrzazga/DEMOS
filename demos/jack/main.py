import os
import time

import pygame
from OpenGL.GL import *

from lib import Globals
from lib.pygame_demo import PygameDemo
from demos.jack.cards import ExitCard, TitleCard
from demos.jack.globe import Globe
from demos.jack.narration import AmbientLoop, Narrator
from demos.jack.overlay import RESOURCES, ScreenOverlay, YearLabel
from lib.photos import PhotoAlbum
from demos.jack.stages import build_stages
from demos.jack.timetable import ClipLibrary, Timetable


class Scene:
    def __init__(self, globe, narrator, year_label):
        self.globe = globe
        self.narrator = narrator
        self.year_label = year_label


class JackDemo(PygameDemo):
    def __init__(self, windowed=False, triggered=False):
        self.fps = 60
        self.longest_frame = 0.1
        self.globe_reveal_seconds = 1.5
        self.audio_folder = os.path.join(RESOURCES, "audio")
        self.ambient_path = os.path.join(RESOURCES, "ambient.mp3")
        super().__init__(1280, 800, "Jack Tramiel", fps=self.fps, windowed=windowed, triggered=triggered)

    def setup(self):
        screen_width, screen_height = pygame.display.get_surface().get_size()
        self._init_gl()
        self.overlay = ScreenOverlay(screen_width, screen_height)
        self.title_card = TitleCard(self.overlay, self.fps)
        self.exit_card = ExitCard()
        self.globe = Globe(screen_width, screen_height)
        self.year_label = YearLabel(screen_height)
        self.narrator = Narrator()
        self.ambient = AmbientLoop(self.ambient_path)
        self.scene = Scene(self.globe, self.narrator, self.year_label)
        self.opening_seconds = self.title_card.duration + self.globe_reveal_seconds
        stages = build_stages(PhotoAlbum(RESOURCES))
        self.timetable = Timetable(stages, ClipLibrary(self.audio_folder), self.opening_seconds)
        self.current_stage = None
        self.ending_started = False
        self.start_ticks = None
        if not self.paused:
            self.on_start()

    def _init_gl(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.92, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.12, 0.14, 0.20, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.10, 0.12, 0.18, 1.0))

    def on_start(self):
        self.ambient.start()
        self.start_ticks = pygame.time.get_ticks()

    def _elapsed(self):
        return (pygame.time.get_ticks() - self.start_ticks) / 1000.0

    def step(self):
        time = self._elapsed()
        dt = min(self.longest_frame, self.clock.get_time() / 1000.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if time < self.title_card.duration:
            self._play_title(time)
            return
        self._follow_timetable(time)
        self._advance(dt, time)
        self._render(time)

    def _play_title(self, time):
        self.title_card.update(time)
        self.overlay.apply()
        self.title_card.draw(self.overlay, time)
        self.overlay.finish()

    def _follow_timetable(self, time):
        stage = self.timetable.stage_at(time)
        if stage is not self.current_stage:
            if self.current_stage is not None:
                self.current_stage.leave(self.scene)
            stage.enter(self.scene)
            self.current_stage = stage

    def _advance(self, dt, time):
        if self.current_stage is not None:
            self.current_stage.update(dt, time, self.scene)
        self.globe.update(dt)
        self.year_label.update(dt)

    def _render(self, time):
        self.globe.draw()
        self.overlay.apply()
        if self.current_stage is not None:
            self.current_stage.draw_overlay(self.overlay, time)
        self.year_label.draw(self.overlay)
        self.overlay.darken(1.0 - (time - self.title_card.duration) / self.globe_reveal_seconds)
        self._play_ending(time - self.timetable.end_time)
        self.overlay.finish()

    def _play_ending(self, seconds):
        if seconds < 0.0:
            return
        if not self.ending_started:
            self.ending_started = True
            self.year_label.show(None)
            self.ambient.fade_out(self.exit_card.duration)
        self.exit_card.draw(self.overlay, seconds)
        if self.exit_card.finished(seconds):
            self.running = False
            print("Demo duration: " + str(Globals.get_duration()))


if __name__ == "__main__":
    JackDemo(windowed=True).run()
