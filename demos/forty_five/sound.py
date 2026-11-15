import pygame


def load_sound(sound_path):
	if not pygame.mixer.get_init():
		pygame.mixer.init()
	return pygame.mixer.Sound(sound_path)
