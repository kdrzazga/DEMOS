import arcade
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.intro import Intro
from demos.demo1.outro import Outro


# e = AnimatedSprite()


class Demo1(arcade.Window):
    def __init__(self):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "Demo 1")

        self.frame = 0
        self.intro = Intro()
        self.outro = Outro()
        arcade.set_background_color(arcade.color.WHITE)

    def on_update(self, delta_time):
        self.frame += 1

        #print(self.frame, end=' ')

        if self.frame < 200:
            self.intro.on_update(self.frame)
        else:
            self.outro.on_update(delta_time)

    def on_draw(self):
        lblue = Color.from_hex_string(Constants.LIGHT_BLUE)
        self.clear(color=lblue)

        if self.frame < 200:
            self.intro.on_draw(self.frame)
        else:
            self.outro.on_draw()

