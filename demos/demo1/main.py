import arcade
from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.intro import Intro
from demos.demo1.outro import Outro
from demos.demo1.stage1 import Stage1
from demos.demo1.stage2 import Stage2
from demos.demo1.stage3 import Stage3
from demos.demo1.stage4 import Stage4
from demos.demo1.stage5 import Stage5
from demos.demo1.stage6 import Stage6


class Demo1(arcade.Window):
    def __init__(self):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "Demo 1", fullscreen=False)

        self.frame = 0
        self.intro = Intro()
        self.stage1 = Stage1()
        self.stage2 = Stage2()
        self.stage3 = Stage3()
        self.stage5 = Stage5()
        self.stage4 = Stage4()
        self.outro = Outro()
        #arcade.set_background_color(arcade.color.WHITE)

    def on_update(self, delta_time):
        self.frame += 1

        #print(self.frame, end=' ')

        if self.frame < Stage1.START_FRAME:
            self.intro.on_update(self.frame)
        elif self.frame < Stage2.START_FRAME:
            self.stage1.on_update(self.frame)
        else:
            self.outro.on_update(delta_time)

    def on_draw(self):
        lblue = Color.from_hex_string(Constants.LIGHT_BLUE)
        self.clear(color=lblue)

        if self.frame < Stage1.START_FRAME:
            self.intro.on_draw(self.frame)

        elif Stage1.START_FRAME < self.frame < Stage2.START_FRAME:
            self.stage1.on_draw(self.frame)
        elif self.frame < Stage3.START_FRAME:
            self.stage2.on_draw(self.frame)
        elif self.frame < Stage4.START_FRAME:
            self.stage3.on_draw(self.frame)
        elif self.frame < Stage5.START_FRAME:
            self.stage4.on_draw(self.frame)
        elif self.frame < Stage6.START_FRAME:
            self.stage5.on_draw(self.frame)

        else:
            self.outro.on_draw()

