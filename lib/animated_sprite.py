import os
from abc import ABC, abstractmethod

os.environ["PATH"] += os.pathsep

import arcade
import pygame

from arcade import Rect
from arcade.color import WHITE


class BaseAnimatedSprite(ABC):
    def __init__(self, spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                 frame_delay):
        self.spritesheet = self.load_spritesheet(spritesheet_path)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frames = [self.cut_frame(index * frame_width, 0, frame_width, frame_height)
                       for index in range(num_frames)]
        self.current_frame = 0
        self.frame_delay = frame_delay
        self.time_since_last_frame = 0
        self.place(position_x, position_y)
        self.show_frame(self.current_texture)

    @abstractmethod
    def load_spritesheet(self, spritesheet_path):
        pass

    @abstractmethod
    def cut_frame(self, x, y, width, height):
        pass

    @abstractmethod
    def place(self, position_x, position_y):
        pass

    def show_frame(self, frame):
        pass

    @property
    def current_texture(self):
        return self.frames[self.current_frame]

    def restart(self):
        self.current_frame = 0
        self.time_since_last_frame = 0
        self.show_frame(self.current_texture)

    def update(self, delta_time):
        self.time_since_last_frame += delta_time
        if self.time_since_last_frame > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.show_frame(self.current_texture)
            self.time_since_last_frame = 0


class AnimatedSprite(BaseAnimatedSprite):
    def __init__(self, spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                 frame_delay=0.2):
        self.sprite = arcade.Sprite()
        super().__init__(spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                         frame_delay)

    def load_spritesheet(self, spritesheet_path):
        return arcade.load_texture(spritesheet_path)

    def cut_frame(self, x, y, width, height):
        return self.spritesheet.crop(x, y, width, height)

    def place(self, position_x, position_y):
        self.sprite.center_x = position_x
        self.sprite.center_y = position_y

    def show_frame(self, frame):
        self.sprite.texture = frame

    def draw(self):
        rect = Rect(
            x=self.sprite.center_x,
            y=self.sprite.center_y,
            width=self.frame_width,
            height=self.frame_height,
            left=self.sprite.center_x,
            right=self.sprite.center_y,
            bottom=0,
            top=0
        )

        arcade.draw_texture_rect(
            texture=self.sprite.texture,
            rect=rect,
            color=WHITE,
            angle=0.0,
            blend=True,
            alpha=255,
            pixelated=False
        )


class PygameAnimatedSprite(BaseAnimatedSprite):
    def __init__(self, spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                 frame_delay):
        self.center_x = position_x
        self.center_y = position_y
        super().__init__(spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                         frame_delay)

    def load_spritesheet(self, spritesheet_path):
        return pygame.image.load(spritesheet_path)

    def cut_frame(self, x, y, width, height):
        return self.spritesheet.subsurface((x, y, width, height))

    def place(self, position_x, position_y):
        self.center_x = position_x
        self.center_y = position_y

    def draw(self, surface):
        frame = self.current_texture
        surface.blit(frame, frame.get_rect(center=(self.center_x, self.center_y)))
