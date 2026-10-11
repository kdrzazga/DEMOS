import pygame


class Soundtrack:
	def __init__(self, path, start_seconds, end_event=pygame.USEREVENT + 1):
		self.path = path
		self.start_seconds = start_seconds
		self.end_event = end_event
		self.playing = False

	def start(self):
		if self.playing:
			return
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		pygame.mixer.music.load(self.path)
		pygame.mixer.music.set_endevent(self.end_event)
		self.play_from_start_point()
		self.playing = True

	def play_from_start_point(self):
		pygame.mixer.music.play(start=self.start_seconds)

	def handle_event(self, event):
		if self.playing and event.type == self.end_event:
			self.play_from_start_point()
