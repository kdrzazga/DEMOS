import arcade

from demos.demo1.main import Demo1
from demos.demo2.main import Demo2


def demo1():
    Demo1()
    arcade.run()


def demo2():
    Demo2()
    arcade.run()


if __name__ == "__main__":
    demo1()
