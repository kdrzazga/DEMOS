import sys

import arcade

from demos.demo1.main import Demo1
from demos.pc45.main import GlDemo
from demos.petscii.files.petsciidemo import PetsciiDemo


def kna_demo(windowed, triggered):
    Demo1(windowed=windowed, triggered=triggered)
    arcade.run()


def pc45_demo(windowed, triggered):
    GlDemo(windowed=windowed, triggered=triggered).run()


def petscii_demo(windowed, triggered):
    PetsciiDemo(windowed=windowed, triggered=triggered).run()


# demo name -> launcher; every launcher takes the same (windowed, triggered)
DEMOS = {
    "kna": kna_demo,
    "pc45": pc45_demo,
    "petscii": petscii_demo,
}

DEFAULT_DEMO = "pc45"


if __name__ == "__main__":
    args = [arg.lower() for arg in sys.argv[1:]]
    triggered = any(arg in ("t", "trigger", "triggered") for arg in args)
    windowed = any(arg in ("w", "window", "windowed") for arg in args)
    name = next((arg for arg in args if arg in DEMOS), DEFAULT_DEMO)
    DEMOS[name](windowed, triggered)
