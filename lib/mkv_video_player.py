import time

import av
import pygame


class MkvVideoPlayer:

	def __init__(self, video_path, loop=False, picture_width=None):
		self.video_path = video_path
		self.loop = loop
		self.container = av.open(video_path)
		self.video_stream = self.container.streams.video[0]
		self.video_stream.thread_type = "AUTO"
		self.width = picture_width or self.video_stream.width
		self.height = max(1, round(self.width * self.video_stream.height / self.video_stream.width))
		self.frames_per_second = float(self.video_stream.average_rate or 30.0)
		self.decoded_frames = self.container.decode(self.video_stream)
		self.pending_frame = None
		self.first_frame_seconds = None
		self.loop_started_at = None
		self.frames_shown_in_this_loop = 0
		self.current_image = None
		self.surface = pygame.Surface((self.width, self.height))
		self.finished = False

	def update(self):
		if self.loop_started_at is None:
			self.loop_started_at = time.perf_counter()
		image_changed = False
		while not self.finished:
			if self.pending_frame is None:
				self.pending_frame = self.decode_next_frame()
			if self.pending_frame is None:
				self.handle_end_of_stream()
				continue
			if self.seconds_from_loop_start(self.pending_frame) > time.perf_counter() - self.loop_started_at:
				break
			self.current_image = self.pending_frame.to_ndarray(width=self.width, height=self.height, format="rgb24")
			self.pending_frame = None
			self.frames_shown_in_this_loop += 1
			image_changed = True
		if image_changed:
			self.surface = pygame.image.frombuffer(self.current_image, (self.width, self.height), "RGB")
		return image_changed

	def decode_next_frame(self):
		try:
			return next(self.decoded_frames, None)
		except av.error.EOFError:
			return None

	def seconds_from_loop_start(self, frame):
		frame_seconds = frame.time
		if frame_seconds is None:
			return self.frames_shown_in_this_loop / self.frames_per_second
		if self.first_frame_seconds is None:
			self.first_frame_seconds = frame_seconds
		return frame_seconds - self.first_frame_seconds

	def handle_end_of_stream(self):
		if not self.loop or self.frames_shown_in_this_loop == 0:
			self.finished = True
			return
		self.rewind()

	def rewind(self):
		self.container.seek(0)
		self.decoded_frames = self.container.decode(self.video_stream)
		self.pending_frame = None
		self.frames_shown_in_this_loop = 0
		self.loop_started_at = time.perf_counter()
		self.finished = False

	def close(self):
		self.container.close()
