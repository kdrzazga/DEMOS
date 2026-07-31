import os

import pygame


class AudioController:
	"""Plays a music track, can fade it, and can swap to a follow-up track once.

	The tracks are passed in - the class knows how to play/fade/swap, but not
	which files or when; that policy stays with the caller.
	"""

	DECAY = 0.99

	def __init__(self, res_path, track, next_track=None):
		self.res_path = res_path
		self.track = track
		self.next_track = next_track
		self.volume = 1.0
		self.switched = False

	def _play(self, filename):
		try:
			pygame.mixer.music.load(os.path.join(self.res_path, filename))
			pygame.mixer.music.set_volume(self.volume)
			pygame.mixer.music.play()
		except pygame.error as exc:
			print("audio unavailable:", exc)

	def start(self):
		self.volume = 1.0
		self.switched = False
		self._play(self.track)

	def update(self, fading, cue_next):
		if self.switched:
			return
		if cue_next and self.next_track:
			self.volume = 1.0
			self._play(self.next_track)
			self.switched = True
			return
		if fading:
			self.volume *= self.DECAY
			pygame.mixer.music.set_volume(self.volume)

	def fade_out(self, step):
		self.volume = max(0.0, self.volume - step)
		pygame.mixer.music.set_volume(self.volume)
