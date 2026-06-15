import pyautogui
import arcade

from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.intro import Intro
from demos.demo1.stage1 import Stage1
from demos.demo1.stage11team import Stage11
from demos.demo1.stage12tunnel2 import Stage12
from demos.demo1.stage13 import Stage13
from demos.demo1.stage2 import Stage2
from demos.demo1.stage3allwhite import Stage3
from demos.demo1.stage4 import Stage4
from demos.demo1.stage5 import Stage5
from demos.demo1.stage7pacman import Stage7
from demos.demo1.stage6 import Stage6
from demos.demo1.stage8dialog1 import Stage8
from demos.demo1.stage9dialog2 import Stage9
from demos.demo1.stage10dialog3 import Stage10
from demos.demo1.outro import Outro


class Demo1(arcade.Window):
    def __init__(self):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "Demo 1", fullscreen=False)

        self.frame = 0 * Stage12.START_FRAME
        self.intro = Intro()
        self.stage1 = Stage1()
        self.stage2 = Stage2()
        self.stage3 = Stage3()
        self.stage4 = Stage4()
        self.stage5 = Stage5()
        self.stage6 = Stage6()
        self.stage7 = Stage7()
        self.stage8 = Stage8()
        self.stage9 = Stage9()
        self.stage10 = Stage10()
        self.stage11 = Stage11()
        self.stage12 = Stage12()
        self.stage13 = Stage13()
        self.outro = Outro()

        self.sound = arcade.load_sound(Constants.RES_PATH + "civ3modernMarkCromer.mp3")
        self.player = None

        width, height = pyautogui.size()
        pyautogui.moveTo(width - 1, height - 1)

        # arcade.set_background_color(arcade.color.WHITE)

    def on_update(self, delta_time):
        self.frame += 1
        # print(self.frame, end=' ')

        if self.frame < Stage1.START_FRAME:
            self.intro.on_update(self.frame)
        elif self.frame < Stage2.START_FRAME:
            self.stage1.on_update(self.frame, Stage1)
        elif Stage7.START_FRAME < self.frame < Stage8.START_FRAME:
            self.stage7.on_update(self.frame, Stage7)
        elif Stage8.START_FRAME < self.frame < Stage9.START_FRAME:
            self.stage8.on_update(self.frame, Stage8)
            if self.player is not None:
                vol = self.player.volume - 0.01
                self.player.volume = max(0.13, vol)
        elif Stage9.START_FRAME < self.frame < Stage10.START_FRAME:
            self.stage9.on_update(self.frame, Stage9)
        elif Stage10.START_FRAME < self.frame < Stage11.START_FRAME:
            self.stage10.on_update(self.frame, Stage10)
        elif Stage11.START_FRAME < self.frame < Stage12.START_FRAME:
            self.stage11.on_update(self.frame, Stage11)
            if self.player is not None:
                vol = self.player.volume + 0.01
                self.player.volume = min(1.0, vol)
        elif Stage12.START_FRAME < self.frame < Stage13.START_FRAME:
            self.stage12.on_update(self.frame,Stage12)
        elif self.frame >= Outro.START_FRAME:
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
        elif self.frame < Stage7.START_FRAME:
            self.stage6.on_draw(self.frame)
        elif self.frame < Stage8.START_FRAME:
            self.stage7.on_draw(self.frame)
        elif self.frame < Stage9.START_FRAME:
            self.stage8.on_draw(self.frame)
        elif self.frame < Stage10.START_FRAME:
            self.stage9.on_draw(self.frame)
        elif self.frame < Stage11.START_FRAME:
            self.stage10.on_draw(self.frame)
        elif self.frame < Stage12.START_FRAME:
            self.stage11.on_draw(self.frame)
        elif self.frame < Stage13.START_FRAME:
            self.stage12.on_draw(self.frame)

        else:
            self.outro.on_draw()

        if self.frame == Stage3.START_FRAME:
            self.player = self.sound.play()

