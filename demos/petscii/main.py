import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.petscii.files.petsciidemo import PetsciiDemo


def petscii_demo(windowed=False, triggered=False):
    PetsciiDemo(windowed=windowed, triggered=triggered).run()
