"""Plays a video clip, with its soundtrack, inside the live OpenGL context.

ffmpeg decodes the picture into raw RGB frames that are uploaded to one GL
texture and drawn on a screen-covering quad, so there is no separate video
window and the scene after it is simply the next frame in the same context.

The soundtrack plays through pygame.mixer.music from a WAV next to the movie;
if the WAV is missing it is extracted from the movie with ffmpeg first. The
picture is clocked off the audio position, so sound and image stay locked and
a slow frame just skips decoded frames to catch up. Without audio it falls back
to the wall clock and plays silently; without ffmpeg or the movie it shows
black for no time at all and reports done straight away.
"""

import json
import os
import shutil
import subprocess

import numpy as np
import pygame
from OpenGL.GL import *


def find_tool(name, env_var, fallback_dirs=(r"D:\ffmpeg\bin", r"C:\ffmpeg\bin")):
	"""Locate an ffmpeg-family executable: env var, then PATH, then fallback_dirs.

	Falls back to the bare name so subprocess raises a clear 'file not found'
	if the tool is genuinely absent.
	"""
	override = os.environ.get(env_var)
	if override:
		return override
	on_path = shutil.which(name)
	if on_path:
		return on_path
	for directory in fallback_dirs:
		candidate = os.path.join(directory, name + ".exe")
		if os.path.exists(candidate):
			return candidate
	return name


class FfmpegFrameReader:
	"""Streams a video's frames as (height, width, 3) uint8 RGB arrays via ffmpeg."""

	def __init__(self, video_path, ffmpeg=None, ffprobe=None):
		self.video_path = video_path
		self.ffmpeg = ffmpeg or find_tool("ffmpeg", "FFMPEG")
		self.ffprobe = ffprobe or find_tool("ffprobe", "FFPROBE")
		self.fps, self.frame_count, self.width, self.height = self._probe()
		self._frame_bytes = self.width * self.height * 3
		self._process = self._open_stream()

	def _probe(self):
		command = [self.ffprobe, "-v", "error", "-select_streams", "v:0",
		           "-show_entries", "stream=r_frame_rate,nb_frames,width,height,duration:format=duration",
		           "-of", "json", self.video_path]
		info = json.loads(subprocess.run(command, capture_output=True, text=True, check=True).stdout)
		stream = info["streams"][0]
		fps = self._parse_fraction(stream.get("r_frame_rate")) or 30.0
		frame_count = self._count_frames(stream, info.get("format", {}), fps)
		return fps, frame_count, int(stream["width"]), int(stream["height"])

	@staticmethod
	def _parse_fraction(text):
		"""ffprobe's "30000/1001" rate as a float; 0.0 if unusable."""
		if not text:
			return 0.0
		numerator, _, denominator = text.partition("/")
		try:
			divisor = float(denominator) if denominator else 1.0
			return float(numerator) / divisor if divisor else 0.0
		except ValueError:
			return 0.0

	@staticmethod
	def _count_frames(stream, container, fps):
		"""The stored frame count, or failing that duration * fps."""
		stored = stream.get("nb_frames")
		if stored and stored != "N/A":
			try:
				return int(stored)
			except ValueError:
				pass
		duration = stream.get("duration") or container.get("duration")
		try:
			return int(round(float(duration) * fps)) if duration else 0
		except (TypeError, ValueError):
			return 0

	def _open_stream(self):
		command = [self.ffmpeg, "-loglevel", "error", "-i", self.video_path,
		           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
		return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

	def read(self):
		"""The next frame as an RGB array, or None at the end of the stream."""
		raw = self._read_exact(self._frame_bytes)
		if raw is None:
			return None
		return np.frombuffer(raw, np.uint8).reshape(self.height, self.width, 3)

	def _read_exact(self, size):
		chunks = []
		remaining = size
		while remaining > 0:
			chunk = self._process.stdout.read(remaining)
			if not chunk:
				return None
			chunks.append(chunk)
			remaining -= len(chunk)
		return b"".join(chunks)

	def release(self):
		if self._process is None:
			return
		if self._process.stdout is not None:
			self._process.stdout.close()
		self._process.terminate()
		try:
			self._process.wait(timeout=1.0)
		except subprocess.TimeoutExpired:
			self._process.kill()
		self._process = None


class IntroVideo:
	"""Plays one clip full-screen (letterboxed to keep its shape), fading out its tail.

	Call render() once per frame until done, then destroy(). It leaves the GL
	state (depth test, lighting, matrices) as it found it, so a 3D scene can be
	drawn right after it in the same context.
	"""

	def __init__(self, video_path, audio_path, window_aspect, fade_ms=500):
		self.video_path = video_path
		self.audio_path = audio_path
		self.window_aspect = window_aspect
		self.fade_ms = fade_ms

		self.capture = self._open_video(video_path)
		self.video_fps = self.capture.fps if self.capture else 30.0
		frame_count = self.capture.frame_count if self.capture else 0
		self.duration_ms = frame_count / self.video_fps * 1000.0
		self.video_aspect = self.capture.width / self.capture.height if self.capture else window_aspect

		self._audio_ok = self._init_audio()
		self.texture = self._make_texture()
		self._start_ms = None
		self._next_index = 0
		self._last_frame = None
		self._exhausted = self.capture is None

	@staticmethod
	def _open_video(path):
		try:
			return FfmpegFrameReader(path)
		except (OSError, subprocess.SubprocessError, ValueError, KeyError):
			return None

	@staticmethod
	def _make_texture():
		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		return texture

	def _init_audio(self):
		if not self._ensure_audio():
			return False
		try:
			if not pygame.mixer.get_init():
				pygame.mixer.init(frequency=44100, size=-16, channels=2)
			pygame.mixer.music.load(self.audio_path)
			return True
		except pygame.error:
			return False

	def _ensure_audio(self):
		"""Extract the soundtrack from the movie if the WAV is missing."""
		if os.path.exists(self.audio_path):
			return True
		try:
			subprocess.run([find_tool("ffmpeg", "FFMPEG"), "-y", "-loglevel", "error",
			                "-i", self.video_path, "-vn", "-ac", "2", "-ar", "44100",
			                "-c:a", "pcm_s16le", self.audio_path], check=True)
		except (OSError, subprocess.SubprocessError):
			return False
		return os.path.exists(self.audio_path)

	def _elapsed_ms(self):
		"""The audio position when the music is playing, the wall clock otherwise."""
		if self._audio_ok:
			position = pygame.mixer.music.get_pos()
			if position >= 0:
				return position
		return pygame.time.get_ticks() - self._start_ms

	def render(self):
		if self._start_ms is None:
			self._start_ms = pygame.time.get_ticks()
			if self._audio_ok:
				try:
					pygame.mixer.music.play()
				except pygame.error:
					self._audio_ok = False
		elapsed_ms = self._elapsed_ms()
		self._decode_up_to(elapsed_ms)

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_LIGHTING)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()

		if self._last_frame is not None:
			self._draw_video_quad()
		fade = self._fade_alpha(elapsed_ms)
		if fade > 0.0:
			self._draw_black(fade)

		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopAttrib()

	def _decode_up_to(self, elapsed_ms):
		"""Decode until the shown frame matches the elapsed time; upload only on change."""
		target = int(elapsed_ms / 1000.0 * self.video_fps)
		stepped = False
		while not self._exhausted and self._next_index <= target:
			frame = self.capture.read()
			if frame is None:
				self._exhausted = True
				break
			self._last_frame = frame
			self._next_index += 1
			stepped = True
		if stepped:
			self._upload(self._last_frame)

	def _upload(self, frame_rgb):
		rgb = np.ascontiguousarray(frame_rgb)
		height, width = rgb.shape[:2]
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, rgb)

	def _video_half_extents(self):
		if self.video_aspect >= self.window_aspect:
			return 1.0, self.window_aspect / self.video_aspect
		return self.video_aspect / self.window_aspect, 1.0

	def _draw_video_quad(self):
		half_width, half_height = self._video_half_extents()
		glEnable(GL_TEXTURE_2D)
		glColor3f(1.0, 1.0, 1.0)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 1.0)
		glVertex2f(-half_width, -half_height)
		glTexCoord2f(1.0, 1.0)
		glVertex2f(half_width, -half_height)
		glTexCoord2f(1.0, 0.0)
		glVertex2f(half_width, half_height)
		glTexCoord2f(0.0, 0.0)
		glVertex2f(-half_width, half_height)
		glEnd()
		glDisable(GL_TEXTURE_2D)

	@staticmethod
	def _draw_black(alpha):
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(0.0, 0.0, 0.0, alpha)
		glBegin(GL_QUADS)
		glVertex2f(-1.0, -1.0)
		glVertex2f(1.0, -1.0)
		glVertex2f(1.0, 1.0)
		glVertex2f(-1.0, 1.0)
		glEnd()

	def _fade_alpha(self, elapsed_ms):
		fade_start = max(0.0, self.duration_ms - self.fade_ms)
		if elapsed_ms <= fade_start:
			return 0.0
		return min(1.0, (elapsed_ms - fade_start) / self.fade_ms)

	@property
	def done(self):
		if self._start_ms is None:
			return self.capture is None
		return (pygame.time.get_ticks() - self._start_ms) >= self.duration_ms

	def destroy(self):
		if self._audio_ok:
			pygame.mixer.music.stop()
		if self.capture is not None:
			self.capture.release()
			self.capture = None
		glDeleteTextures([self.texture])
