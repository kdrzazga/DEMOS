import os
import shutil
import subprocess

import cv2
import numpy as np
import pygame
from OpenGL.GL import *

from demos.demo3.files.base_stage import BaseStage


class Intro(BaseStage):
    """Plays the intro movie (iny.mp4) straight into the live OpenGL context.

    There is no separate video window and no framework switch: every decoded
    frame is uploaded to a single GL texture and drawn on a screen-filling quad,
    so the hand-off to the 3D Stage1 is just the next frame in the same context.

    OpenCV decodes only the picture, so the soundtrack is played separately
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

        self.capture = cv2.VideoCapture(os.path.join(res_path, self.movie))
        self.video_fps = self.capture.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = self.capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        self.duration_ms = frame_count / self.video_fps * 1000.0

        self.audio_path = os.path.join(res_path, self.audio)
        self._audio_ok = self._init_audio()

        self.texture = self.make_texture()
        self._start_ms = None       # set on the first rendered frame
        self._next_index = 0        # index of the next frame to decode
        self._last_frame = None     # most recently decoded frame (BGR)
        self._exhausted = False

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
        ffmpeg = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
        if not ffmpeg:
            return False
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
            ok, frame = self.capture.read()
            if not ok:
                self._exhausted = True
                break
            self._last_frame = frame
            self._next_index += 1
            stepped = True
        if stepped:
            self._upload(self._last_frame)

    def _upload(self, frame_bgr):
        rgb = np.ascontiguousarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
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
