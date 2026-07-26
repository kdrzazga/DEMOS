import arcade

from demos.pc45 import Constants
from demos.pc45.intro import Intro


class Demo2(arcade.Window):
    def __init__(self, triggered=False):
        super().__init__(Constants.WIDTH, Constants.HEIGHT, "Demo 2", fullscreen=False)

        self.paused = triggered
        self.frame = 0 #* Stage13.START_FRAME
        self.intro = Intro()
        self.sound = arcade.load_sound(Constants.RES_PATH + "pc-boot.mp3")
        if not self.paused:
            self.sound.play(loop=False)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.paused:
            self.paused = False
            self.sound.play(loop=False)

    def on_update(self, delta_time):
        if self.paused:
            return
        self.frame += 1

    def on_draw(self):
        self.intro.on_draw(self.frame)
