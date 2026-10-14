import pygame


class Narrator:
    def __init__(self, channel_index=0, volume=1.0):
        pygame.mixer.set_reserved(channel_index + 1)
        self.channel = pygame.mixer.Channel(channel_index)
        self.channel.set_volume(volume)

    def play(self, clip):
        self.channel.play(clip.sound)

    def stop(self):
        self.channel.stop()


class AmbientLoop:
    def __init__(self, path, volume=0.3):
        self.path = path
        self.volume = volume

    def start(self):
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(loops=-1)

    def fade_out(self, seconds):
        pygame.mixer.music.fadeout(int(seconds * 1000))
