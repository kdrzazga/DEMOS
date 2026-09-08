import os

import pygame


class SoundAndTalk:

    def __init__(self, outro_sound_file, talk, captions_manager):
        self.outro_sound_file = outro_sound_file
        self.captions_manager = captions_manager
        self.talk = talk
        self.resources_dir = os.path.join(os.path.dirname(__file__), "../resources")
        self.sound = None
        self.channel = None
        self.started = False
        self.was_audible = False
        self.finished = False

    def start(self):
        self.sound = pygame.mixer.Sound(os.path.join(self.resources_dir, self.outro_sound_file))
        self.channel = self.sound.play()
        self.started = True
        self.was_audible = False
        self.finished = False

    def update(self):
        if not self.started or self.finished:
            return
        self.captions_manager.update()
        if self.channel is None:
            self.finished = True
            return
        if self.channel.get_busy():
            self.was_audible = True
        elif self.was_audible:
            self.finished = True

    def draw(self):
        self.captions_manager.draw()

    def talking(self):
        return self.started and not self.finished

    def stop(self):
        if self.sound is not None:
            self.sound.stop()
        self.finished = True
