import math

import arcade
#import cv2
from arcade import Rect, Text
from arcade.types import Color

from demos.demo1 import Constants, Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage14 import Stage14


class Outro(Demo1Base):

	START_FRAME = Stage14.START_FRAME + 440
	DIMINISH_PHASE_FRAME = START_FRAME + 600
	pass

	def __init__(self):
		super().__init__()

		self.video_capture = None #cv2.VideoCapture('resources/TramielHaHa.mp4')
		self.frame = None
		self.texts = (("THANKS FOR WATCHING", 200, 11, 2.5)
		              , ("PLEASE VISIT WWW.KA-PLUS.PL", 300, 14, 3.5)
		              , ("CODE & GFX: KD", 350, 17, 2.5)
		              , ("MSX: MARK CROMER", 400, 20, 2.1))

	def on_draw(self, frame):
		super().on_draw(frame)
		relative_frame = frame - Outro.START_FRAME
		c = Color.from_hex_string(Constants.LIGHT_BLUE)

		cursor_x = 0
		cursor_y = 9*12+7

		text_color = Constants.WHITE
		text_struct = self.texts
		for t in text_struct:
			if relative_frame > t[1]:
				c = Color.from_hex_string(text_color)
				x = Constants.WIDTH*0.1
				y = t[2]*12+5
				Text(text=t[0], x=x, y=Constants.HEIGHT*0.9 - y - 2, color=c, font_size=self.font_size, anchor_x="left"
				     , anchor_y="center", font_name="C64 Pro Mono").draw()
				cursor_y = y
				cursor_x = len(t[0]) + t[3]

		self.blink_cursor(relative_frame, c, cursor_x, cursor_y)

		if frame > Outro.DIMINISH_PHASE_FRAME:
			rect = self.create_bkg_rect()
			frames_since_diminish = frame - Outro.DIMINISH_PHASE_FRAME
			even_frames_passed = frames_since_diminish * 3.6
			transparency = min(255, even_frames_passed)

			color = (96, 96, 192, transparency)
			arcade.draw_rect_filled(rect, color=color)
			#self.draw_cover_arcade_color(color)

			if frame > Outro.DIMINISH_PHASE_FRAME + 240:
				print()
				print(self.texts[0][0])
				print(self.texts[1][0])
				print()
				print("Bye !")
				print(Globals.get_duration())
				arcade.exit()

		return
		if frame is not None:
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

		return
		ret, frame = self.video_capture.read()
		if ret:
			self.frame = frame
		else:
			pass#self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video

	def on_close(self):
				self.video_capture.release()
