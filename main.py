import contextlib
import io
import sys


def _verbose_requested():
    return any(arg.lower() in ("v", "verbose") for arg in sys.argv[1:])


def _import_arcade(verbose):
    """Import arcade. Unless verbose, swallow only its 'Running without PyMunk'
    notice -- arcade prints that with a bare print() to stdout (not logging or
    warnings) when this interpreter can't load the optional pymunk hitbox backend,
    so it can only be filtered at the stream level. Anything else arcade prints
    during import is passed through untouched."""
    if verbose:
        import arcade
        return arcade
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        import arcade
    kept = "".join(line for line in buffer.getvalue().splitlines(keepends=True)
                   if "Running without PyMunk" not in line)
    if kept:
        sys.stdout.write(kept)
    return arcade


arcade = _import_arcade(_verbose_requested())

from demos.demo1.main import Demo1
from demos.demo3.main import Demo3
from demos.pc45.main import GlDemo
from demos.pixeloveole.main import PixeloveOle
from demos.petscii.files.petsciidemo import PetsciiDemo


def kna_demo(windowed, triggered):
    Demo1(windowed=windowed, triggered=triggered)
    arcade.run()


def pc45_demo(windowed, triggered):
    GlDemo(windowed=windowed, triggered=triggered).run()


def petscii_demo(windowed, triggered):
    PetsciiDemo(windowed=windowed, triggered=triggered).run()


def demo3(windowed, triggered):
    Demo3(windowed=windowed, triggered=triggered).run()


def pixelove_ole(windowed, triggered):
    PixeloveOle(windowed=windowed, triggered=triggered).run()


# demo name -> launcher; every launcher takes the same (windowed, triggered)
DEMOS = {
    "kna": kna_demo,
    "pc45": pc45_demo,
    "p3dscii": petscii_demo,
    "demo3": demo3,
    "po": pixelove_ole, #cannot be built to exe, due to execution loop
}

DEFAULT_DEMO = "p3dscii"


def close_boot_splash():
    """Dismiss the PyInstaller 'DECRUNCHING' boot splash. The module only exists
    inside a frozen build that was bundled with a splash, so it's a no-op when
    running from source."""
    try:
        import pyi_splash  # injected by PyInstaller when the exe has a splash
    except ImportError:
        return
    try:
        pyi_splash.close()
    except Exception:
        pass


if __name__ == "__main__":
    #print("Bienvenido a la DEMO de P3DSCII !!! / Welcome to P3DSCII demo !!!")
    args = [arg.lower() for arg in sys.argv[1:]]
    triggered = any(arg in ("t", "trigger", "triggered") for arg in args)
    windowed = any(arg in ("w", "window", "windowed") for arg in args)
    name = next((arg for arg in args if arg in DEMOS), DEFAULT_DEMO)
    # extraction + the heavy arcade/pyglet imports above are done; the demo window
    # opens next, so drop the splash now.
    close_boot_splash()
    DEMOS[name](windowed, triggered)
