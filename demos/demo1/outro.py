import math

import arcade
#import cv2
from arcade import Rect

from demos.demo1 import Constants, Globals
from demos.demo1.base import Demo1Base


class Outro(Demo1Base):

	START_FRAME = math.inf
	pass

	def __init__(self):
		super().__init__()

		self.video_capture = None #cv2.VideoCapture('resources/TramielHaHa.mp4')
		self.frame = None

	def on_draw(self):
		super().on_draw(self.frame)
		pass
		if self.frame is not None:
			# Convert BGR to RGB
			rgb_frame = None#cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
			height, width, _ = rgb_frame.shape

			left = 0.1 * Constants.WIDTH
			bottom = 0.1 * Constants.HEIGHT
			right = left + width
			self.top = bottom + height
			x = left + width // 2
			y = bottom + height // 2
			r = Rect(left, right, bottom, self.top, width, height, x, y)
			#r = Rect(0, Constants.WIDTH, 0, Constants.HEIGHT, Constants.WIDTH, Constants.HEIGHT, 0, 0)
			arcade.draw_texture_rect(
				texture=arcade.Texture(image=rgb_frame),
				rect=r
			)

	def on_update(self, frame, delta_time):

		relative_frame = frame - Outro.START_FRAME
		if relative_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		ret, frame = self.video_capture.read()
		if ret:
			self.frame = frame
		else:
			pass#self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video

	def on_close(self):
				self.video_capture.release()
