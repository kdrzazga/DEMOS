import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.petscii.files.app import App


def petscii_demo():
    App().run()


if __name__ == "__main__":
    petscii_demo()
