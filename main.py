import sys

import arcade

from demos.demo1.main import Demo1
from demos.pc45.main import Demo2


def kna_demo(triggered=False):
    Demo1(triggered)
    arcade.run()


def pc45_demo(triggered=False):
    Demo2(triggered)
    arcade.run()
    arcade.Sprite()


if __name__ == "__main__":
    triggered = any(arg.lower() in ("t", "trigger", "triggered") for arg in sys.argv[1:])
    #pc45_demo(triggered)
    kna_demo(triggered)
