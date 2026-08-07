class BaseDemo:
    """Launch parameters shared by every demo, regardless of the graphics
    framework it is built on (arcade or pygame + OpenGL).

    Two knobs are unified across all demos:

    * ``windowed``  - run in a window instead of fullscreen. Fullscreen is the
      default; pass ``windowed=True`` while developing.
    * ``triggered`` - start paused on a blank screen and only begin on the
      first mouse click. Very handy for lining up a screen recording.

    Framework-specific subclasses wire their own event system to :meth:`trigger`
    and override :meth:`on_start` to kick off music / audio when the demo
    actually begins.
    """

    def __init__(self, windowed=False, triggered=False):
        self.windowed = windowed
        self.triggered = triggered
        self.paused = triggered

    def trigger(self):
        """Leave the triggered-start pause. Safe to call on every mouse click:
        it only does something the first time, while still paused."""
        if self.paused:
            self.paused = False
            self.on_start()

    def on_start(self):
        """Called once, when a triggered demo actually begins. Override to
        start music / audio. No-op by default."""
