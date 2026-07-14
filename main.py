import arcade

from demos.demo1.main import Demo1
from demos.pc45.main import Demo2


def kna_demo():
    Demo1()
    arcade.run()


def pc45_demo():
    Demo2()
    arcade.run()
    arcade.Sprite()


if __name__ == "__main__":
    #pc45_demo()
    kna_demo()
