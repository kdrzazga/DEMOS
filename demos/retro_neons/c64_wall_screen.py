import os

import numpy
from OpenGL.GL import glDeleteTextures

from demos.retro_neons.scene_mirror import SceneMirror
from lib.wall_screen import WallScreen
from lib.c64_screen import C64Screen
from lib.particles import Texture2D
from lib.plasma import PlasmaField
from lib.mkv_video_player import MkvVideoPlayer


class PlasmaPicture:

    def __init__(self, pixel_width, pixel_height):
        self.speed = 0.8
        self.brightness = 0.9
        self.time = 0.0
        self.field = PlasmaField(pixel_width, pixel_height)
        self.pixels = numpy.full((pixel_height, pixel_width, 4), 255, dtype=numpy.uint8)
        self.texture = None

    def prepare(self):
        self.texture = Texture2D(self._painted())

    def update(self, seconds):
        self.time += seconds
        self.texture.update(self._painted())

    def _painted(self):
        colors = self.field.colors_at(self.time * self.speed)
        self.pixels[:, :, :3] = (255.0 * self.brightness * colors).astype(numpy.uint8)
        return self.pixels


class LetterboxedClip:

    def __init__(self, video_path, screen_aspect, picture_width):
        self.video_path = video_path
        self.player = MkvVideoPlayer(video_path, picture_width=picture_width)
        video_width, video_height = self.player.width, self.player.height
        canvas_width = max(video_width, round(video_height * screen_aspect))
        canvas_height = max(video_height, round(video_width / screen_aspect))
        self.left = (canvas_width - video_width) // 2
        self.top = (canvas_height - video_height) // 2
        self.pixels = numpy.zeros((canvas_height, canvas_width, 4), dtype=numpy.uint8)
        self.pixels[:, :, 3] = 255
        self.texture = Texture2D(self.pixels)

    @property
    def finished(self):
        return self.player.finished

    def update(self):
        if not self.player.update():
            return
        video_height, video_width = self.player.current_image.shape[:2]
        self.pixels[self.top:self.top + video_height, self.left:self.left + video_width, :3] = self.player.current_image
        self.texture.update(self.pixels)

    def destroy(self):
        self.player.close()
        glDeleteTextures([self.texture.id])


class C64WallScreen(WallScreen):

    def __init__(self, face, across, rise, width):
        super().__init__(face, across, rise, width)
        self.plasma_glow_color = (0.6, 0.5, 0.9)
        self.clip_glow_color = (0.6, 0.6, 0.7)
        self.c64_seconds_between_clips = 4.0
        self.clip_picture_width = 640
        resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        self.clip_paths = [os.path.join(resources, "meet-the-team.mkv"),
                           os.path.join(resources, "winter-ka.mkv"),
                           os.path.join(resources, "FACES.mkv")
                           ]
        self.plasma = PlasmaPicture(128, 88)
        self.c64 = None
        self.showing_c64 = False
        self.c64_seconds_shown = 0.0
        self.next_clip_index = 0
        self.playing_clip = None
        self.finished_clip_count = 0

    @property
    def playing_clip_name(self):
        return None if self.playing_clip is None else os.path.basename(self.playing_clip.video_path)

    @property
    def every_clip_played(self):
        return self.finished_clip_count >= len(self.clip_paths)

    def prepare(self):
        self.c64 = C64Screen()
        self.place(self.width / self.c64.aspect)
        self.plasma.prepare()

    def switch_on(self):
        self.showing_c64 = True
        self.c64_seconds_shown = 0.0
        self.c64.restart_typing()

    def update(self, seconds):
        if self.playing_clip is not None:
            self.update_playing_clip()
        elif self.showing_c64:
            self.update_c64(seconds)
        else:
            self.plasma.update(seconds)

    def update_c64(self, seconds):
        self.c64.update(seconds)
        self.c64.refresh()
        self.c64_seconds_shown += seconds
        if self.clip_paths and self.c64_seconds_shown >= self.c64_seconds_between_clips:
            self.start_next_clip()

    def start_next_clip(self):
        clip_path = self.clip_paths[self.next_clip_index]
        self.next_clip_index = (self.next_clip_index + 1) % len(self.clip_paths)
        self.playing_clip = LetterboxedClip(clip_path, self.c64.aspect, self.clip_picture_width)

    def update_playing_clip(self):
        self.playing_clip.update()
        if self.playing_clip.finished:
            self.playing_clip.destroy()
            self.playing_clip = None
            self.finished_clip_count += 1
            self.c64_seconds_shown = 0.0

    def draw(self):
        with SceneMirror().readable_texturing():
            if self.playing_clip is not None:
                self.draw_picture(self.playing_clip.texture.id, self.clip_glow_color)
            elif self.showing_c64:
                self.draw_picture(self.c64.texture_id, self.c64.border_color)
            else:
                self.draw_picture(self.plasma.texture.id, self.plasma_glow_color)
