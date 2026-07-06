import arcade
import random
import numpy as np
import sounddevice as sd
from arcade import Text

#t = np.linspace(0, 0.2, int(44100 * 0.2), endpoint=False)
# print(len(t))

def play_beep(frequency=440, duration=0.02, sample_rate=44100):

    t = np.linspace(0, duration, int(sample_rate * duration*20), endpoint=False)

    audio = 5 * np.sin(2 * np.pi * frequency * t)
    sd.play(audio, sample_rate)
    sd.wait()


class Typer:

	def __init__(self, x:int, y:int, font_file:str, font_name:str, font_size:int, color):
		self.x = x
		self.y = y

		arcade.load_font("lib/resources/" + font_file)
		self.font_name = font_name # needs to match the font name from the file read above
		self.font_size = font_size
		self.color = color
		self.typing_progress = 1

	def type(self, message:str, y=-1):

		if self.typing_progress > len(message):
			self.typing_progress = 1
			return

		if y == -1:
			y = self.y

		txt = Text(message[:self.typing_progress],
		     x=self.x,
			y=y,
			font_name=self.font_name,
			font_size=self.font_size,
			color=self.color)

		#print(message[:self.typing_progress])

		frequency = 4*440 * random.randint(1, 4)
		play_beep(frequency)
		txt.draw()

		self.typing_progress += 1
