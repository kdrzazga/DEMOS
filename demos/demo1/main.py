import pyautogui
import arcade

from arcade.types import Color

from demos.demo1 import Constants
from demos.demo1.intro import Intro
from demos.demo1.stage1 import Stage1
from demos.demo1.stage11team import Stage11
from demos.demo1.stage12ikplus import Stage12
from demos.demo1.stage13 import Stage13
from demos.demo1.stage14 import Stage14
from demos.demo1.stage2 import Stage2
from demos.demo1.stage3allwhite import Stage3
from demos.demo1.stage4 import Stage4
from demos.demo1.stage5 import Stage5
from demos.demo1.stage7pacman import Stage7
from demos.demo1.stage6shining import Stage6
from demos.demo1.stage8dialog1 import Stage8
from demos.demo1.stage9dialog2 import Stage9
from demos.demo1.stage10dialog3 import Stage10
from demos.demo1.outro import Outro

from lib.base_demo import BaseDemo


class Demo1(arcade.Window, BaseDemo):
    def __init__(self, windowed=False, triggered=False):
        arcade.Window.__init__(self, Constants.WIDTH, Constants.HEIGHT,
                               "Komoda & Amiga +", fullscreen=not windowed)
        BaseDemo.__init__(self, windowed=windowed, triggered=triggered)

        # Fit the fixed 800x600 world into the physical window without distortion.
        # In fullscreen the window is the monitor's native resolution, so the world
        # is scaled up and pillar/letter-boxed with black bars around it.
        self.scale_cam = arcade.Camera2D(
            position=(0.0, 0.0),  # world (0,0) at the viewport's bottom-left
            projection=arcade.LRBT(0, Constants.WIDTH, 0, Constants.HEIGHT),
            viewport=arcade.LBWH(0, 0, self.width, self.height),
        )
        self._fit_world_to_window()

        self.frame = 0 * Stage7.START_FRAME
        self.intro = Intro()
        if not self.paused:
            self.intro.play_music()
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

    def on_start(self):
        self.intro.play_music()

    def on_mouse_press(self, x, y, button, modifiers):
        self.trigger()

    def _fit_world_to_window(self):
        """Scale the world uniformly into the largest centred rectangle that fits
        the window, preserving the 4:3 aspect ratio (black bars fill the rest).
        The scissor clips off-world sprites/text at the world edge, exactly as the
        window edge did when running 1:1."""
        scale = min(self.width / Constants.WIDTH, self.height / Constants.HEIGHT)
        vp_w = Constants.WIDTH * scale
        vp_h = Constants.HEIGHT * scale
        vp_x = (self.width - vp_w) / 2
        vp_y = (self.height - vp_h) / 2
        rect = arcade.LBWH(vp_x, vp_y, vp_w, vp_h)
        self.scale_cam.viewport = rect
        self.scale_cam.scissor = rect

    def on_resize(self, width, height):
        super().on_resize(width, height)
        if getattr(self, "scale_cam", None) is not None:
            self._fit_world_to_window()

    def on_update(self, delta_time):
        if self.paused:
            return
        self.frame += 1

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
            self.stage12.on_update(self.frame, Stage12)
        elif Stage13.START_FRAME < self.frame < Stage14.START_FRAME:
            self.stage13.on_update(self.frame, Stage13)
        elif self.frame >= Outro.START_FRAME:
            self.outro.on_update(self.frame, delta_time)

        if self.frame > Outro.DIMINISH_PHASE_FRAME - 50 and self.player is not None:
            vol = self.player.volume - 0.005
            self.player.volume = max(0.0, vol)

    def on_draw(self):
        self.default_camera.use()             # full window, no scissor
        self.clear(color=arcade.color.BLACK)  # paints the letterbox bars
        self.scale_cam.use()                  # map the 800x600 world into the viewport

        lblue = Color.from_hex_string(Constants.LIGHT_BLUE)
        arcade.draw_rect_filled(arcade.LBWH(0, 0, Constants.WIDTH, Constants.HEIGHT), color=lblue)

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
        elif self.frame < Stage14.START_FRAME:
            self.stage13.on_draw(self.frame)

        else:
            self.outro.on_draw(self.frame)

        if self.frame == Stage3.START_FRAME:
            self.player = self.sound.play()

