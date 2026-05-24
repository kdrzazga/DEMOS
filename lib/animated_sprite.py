import arcade

from arcade import Rect
from arcade.color import WHITE


class AnimatedSprite:
    def __init__(self, spritesheet_path, position_x, position_y, frame_width, frame_height, num_frames,
                 frame_delay=0.2):
        self.spritesheet = arcade.load_texture(spritesheet_path)
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.frames = []
        for i in range(num_frames):
            x = i * frame_width
            y = 0
            # cut area (x, y, x + frame_width, y + frame_height)  from self.spritesheet
            frame = self.spritesheet.crop(x, y, frame_width, frame_height)
            self.frames.append(frame)

        self.sprite = arcade.Sprite()
        self.sprite.texture = self.frames[0]
        self.sprite.center_x = position_x
        self.sprite.center_y = position_y
        self.current_frame = 0
        self.frame_delay = frame_delay
        self.time_since_last_frame = 0

    def update(self, delta_time):
        self.time_since_last_frame += delta_time
        if self.time_since_last_frame > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.sprite.texture = self.frames[self.current_frame]
            self.time_since_last_frame = 0
            print("texture chnge")

    def draw(self):
        window = arcade.get_window()
        current_width = window.width
        current_height = window.height

        rect = Rect(
            x=current_width // 2,  # center x
            y=current_height // 2,  # center y
            width=self.frame_width,
            height=self.frame_height,
            left=current_width // 2,  # optional, defaults to x - width/2
            right=current_height // 2,  # optional, defaults to x + width/2
            bottom=0,  # optional, defaults to y - height/2
            top=0  # optional, defaults to y + height/2
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
