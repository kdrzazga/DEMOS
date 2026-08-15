import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import arcade

from lib.textwall import TextWallArray, ArcadeTextWall
from lib.test.corpus import load_text, build_lines

WIDTH, HEIGHT = 800, 600
GREEN = (51, 255, 102)
BLUE = (102, 204, 255)


class ScrollTest(arcade.Window):

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "TextWall - arcade")
        self.background_color = (0, 0, 0)
        layout = dict(x=16, y=12, initial_screen_y=260, rows=25,
                      speed=20, loop=False, font_size=12)
        wall_a = ArcadeTextWall(build_lines(load_text("kaplus.txt")), screen_height=HEIGHT,
                                color=GREEN, **layout)
        wall_b = ArcadeTextWall(build_lines(load_text("karate.txt")), screen_height=HEIGHT,
                                color=BLUE, **layout)
        self.walls = TextWallArray()
        self.walls.add(wall_a, 0.0)
        self.walls.add(wall_b, 0.5)

    def on_update(self, delta_time):
        self.walls.update(delta_time)

    def on_draw(self):
        self.clear()
        self.walls.draw()


if __name__ == "__main__":
    ScrollTest()
    arcade.run()
