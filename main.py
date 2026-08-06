import sys

import arcade

from demos.demo1.main import Demo1
from demos.pc45.main import GlDemo


def kna_demo(triggered=False):
    Demo1(triggered)
    arcade.run()


def pc45_demo(windowed, triggered):
    GlDemo(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
    triggered = any(arg.lower() in ("t", "trigger", "triggered") for arg in sys.argv[1:])
    windowed = any(arg.lower() in ("w", "window", "windowed") for arg in sys.argv[1:])
    pc45_demo(windowed, triggered)
    #kna_demo(triggered)
