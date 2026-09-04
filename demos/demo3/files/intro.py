import json
import os
import shutil
import subprocess

import numpy as np
import pygame
from OpenGL.GL import *

from demos.demo3.files.base_stage import BaseStage


# ffmpeg is frequently unpacked outside PATH on Windows; these dirs are tried
# only after an explicit env var (FFMPEG/FFPROBE) and PATH both come up empty.
_FFMPEG_FALLBACK_DIRS = (
    r"D:\ffmpeg\bin",
    r"C:\ffmpeg\bin",
)


def _find_tool(name, env_var):
    """Locate an ffmpeg-family executable, preferring an explicit env var, then
    PATH, then the common install dirs above. Falls back to the bare name so
    subprocess raises a clear 'file not found' if it is genuinely absent."""
    override = os.environ.get(env_var)
    if override:
        return override
    on_path = shutil.which(name)
    if on_path:
        return on_path
    for directory in _FFMPEG_FALLBACK_DIRS:
        candidate = os.path.join(directory, name + ".exe")
        if os.path.exists(candidate):
            return candidate
    return name


class FfmpegFrameReader:
    """Decodes a video into raw RGB frames with ffmpeg, replacing OpenCV.

    ffprobe supplies the geometry (fps, frame count, size) up front, then ffmpeg
    streams the picture as rgb24 to a pipe. Each ``read`` returns the next frame
    as a ``(height, width, 3)`` uint8 array already in RGB order, so it can go
    straight to the GL texture with no colour swap.
    """

    def __init__(self, video_path, ffmpeg=None, ffprobe=None):
        self.video_path = video_path
        self.ffmpeg = ffmpeg or _find_tool("ffmpeg", "FFMPEG")
        self.ffprobe = ffprobe or _find_tool("ffprobe", "FFPROBE")
        self.fps, self.frame_count, self.width, self.height = self._probe()
        self._frame_bytes = self.width * self.height * 3
        self._process = self._open_stream()

    def _probe(self):
        command = [self.ffprobe, "-v", "error", "-select_streams", "v:0",
                   "-show_entries",
                   "stream=r_frame_rate,nb_frames,width,height,duration"
                   ":format=duration",
                   "-of", "json", self.video_path]
        info = json.loads(subprocess.run(
            command, capture_output=True, text=True, check=True).stdout)
        stream = info["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
        fps = self._parse_fraction(stream.get("r_frame_rate")) or 30.0
        frame_count = self._count_frames(stream, info.get("format", {}), fps)
        return fps, frame_count, width, height

    @staticmethod
    def _parse_fraction(text):
        """Turn ffprobe's ``"30000/1001"`` rate into a float; 0.0 if unusable."""
        if not text:
            return 0.0
        numerator, _, denominator = text.partition("/")
        try:
            den = float(denominator) if denominator else 1.0
            return float(numerator) / den if den else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def _count_frames(stream, container, fps):
        """Prefer the stored frame count; if the container did not record one,
        derive it from the duration and the frame rate."""
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
        return subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)

    def read(self):
        """Return the next frame as an RGB array, or None at end of stream."""
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
                return None            # EOF before a full frame -> end of video
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


class Intro(BaseStage):
    """Plays the intro movie (iny.mp4) straight into the live OpenGL context.

    There is no separate video window and no framework switch: every decoded
    frame is uploaded to a single GL texture and drawn on a screen-filling quad,
    so the hand-off to the 3D Stage1 is just the next frame in the same context.

    ffmpeg decodes only the picture, so the soundtrack is played separately
    through ``pygame.mixer`` from a WAV sibling of the movie (``iny.wav``). The
    video is then clocked off the *audio* position, which keeps picture and
    sound locked together and lets the render loop run at whatever rate it can;
    a dropped render frame just skips decoded frames to catch back up. With no
    audio available it falls back to the wall clock and plays silently.
    """

    def __init__(self, win_w, win_h, res_path, fov):
        super().__init__(win_w, win_h, res_path, fov)

        self.movie = "iny.mp4"
        self.audio = "iny.wav"
        self.fade_ms = 500          # fade the tail of the clip to black
        self.background = (0.0, 0.0, 0.0)

        self.capture = self._open_video(os.path.join(res_path, self.movie))
        self.video_fps = self.capture.fps if self.capture else 30.0
        frame_count = self.capture.frame_count if self.capture else 0
        self.duration_ms = frame_count / self.video_fps * 1000.0

        self.audio_path = os.path.join(res_path, self.audio)
        self._audio_ok = self._init_audio()

        self.texture = self.make_texture()
        self._start_ms = None       # set on the first rendered frame
        self._next_index = 0        # index of the next frame to decode
        self._last_frame = None     # most recently decoded frame (RGB)
        self._exhausted = self.capture is None

    @staticmethod
    def _open_video(path):
        """Build the frame reader, or None if ffmpeg/ffprobe or the movie are
        unavailable - in which case the intro shows black and skips through,
        exactly as it did before when a clip could not be opened."""
        try:
            return FfmpegFrameReader(path)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            return None

    # ---- audio ----------------------------------------------------------
    def _init_audio(self):
        """Load the soundtrack for playback, extracting it from the movie first
        if the WAV is missing (and an ffmpeg can be found). Returns False - and
        the intro plays silently - if none of that pans out."""
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
        if os.path.exists(self.audio_path):
            return True
        ffmpeg = _find_tool("ffmpeg", "FFMPEG")
        try:
            subprocess.run([ffmpeg, "-y", "-loglevel", "error",
                            "-i", os.path.join(self.res_path, self.movie),
                            "-vn", "-ac", "2", "-ar", "44100",
                            "-c:a", "pcm_s16le", self.audio_path], check=True)
        except (OSError, subprocess.SubprocessError):
            return False
        return os.path.exists(self.audio_path)

    def _elapsed_ms(self):
        """Prefer the audio playback position so the picture tracks the sound;
        fall back to the wall clock before the music starts or after it ends."""
        if self._audio_ok:
            pos = pygame.mixer.music.get_pos()
            if pos >= 0:
                return pos
        return pygame.time.get_ticks() - self._start_ms

    # ---- frame ----------------------------------------------------------
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

        glClearColor(*self.background, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self._last_frame is not None:
            self._draw_video_quad()

        fade = self._fade_alpha(elapsed_ms)
        if fade > 0.0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            self.fill_screen(0.0, 0.0, 0.0, fade)
            glDisable(GL_BLEND)

        self.frame += 1

    def _decode_up_to(self, elapsed_ms):
        """Advance decoding so the shown frame matches the elapsed time. Uploads
        to the texture only if we actually stepped to a new frame."""
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
        h, w = rgb.shape[:2]
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)   # rows are not 4-byte aligned
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, rgb)

    def _draw_video_quad(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        # The frame's first row is its top, so v=0 maps to the top of the screen.
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, 1.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def _fade_alpha(self, elapsed_ms):
        fade_start = max(0.0, self.duration_ms - self.fade_ms)
        if elapsed_ms <= fade_start:
            return 0.0
        return min(1.0, (elapsed_ms - fade_start) / self.fade_ms)

    @property
    def done(self):
        if self._start_ms is None:
            return False
        return (pygame.time.get_ticks() - self._start_ms) >= self.duration_ms

    def destroy(self):
        if self._audio_ok:
            pygame.mixer.music.stop()
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        glDeleteTextures([self.texture])
