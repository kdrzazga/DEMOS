import pygame
from pygame.locals import DOUBLEBUF, FULLSCREEN, KEYDOWN, K_ESCAPE, MOUSEBUTTONDOWN, OPENGL, QUIT
from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear

from lib.base_demo import BaseDemo


class PygameDemo(BaseDemo):
    """Base for pygame + OpenGL demos.

    Owns the window and the main loop, and handles the events that every demo
    shares: quit on ESC / window close, and un-pause a triggered start on the
    first mouse click. Subclasses fill in the per-demo pieces:

    * :meth:`setup` - one-time GL state / resource loading, run after the window
      exists but before the loop (and before the initial pause is applied).
    * :meth:`step`  - advance and render a single frame; only called while the
      demo is running (i.e. not paused).

    and may override :meth:`handle_event` (extra keys), :meth:`render_paused`
    (the blank holding frame), :meth:`on_pause` (entering the triggered pause)
    and :meth:`on_start` (leaving it).
    """

    def __init__(self, width, height, title, fps=60, opengl=True,
                 windowed=False, triggered=False):
        super().__init__(windowed=windowed, triggered=triggered)
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps

        pygame.init()
        flags = 0
        if opengl:
            flags |= DOUBLEBUF | OPENGL
        if not self.windowed:
            flags |= FULLSCREEN
        pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)

        self.clock = pygame.time.Clock()
        self.running = False

        self.setup()
        if self.paused:
            self.on_pause()

    # ---- template hooks -------------------------------------------------
    def setup(self):
        """One-time GL state and resource loading. Override."""

    def step(self):
        """Advance and render one frame. Override."""

    def handle_event(self, event):
        """Handle a demo-specific event (extra keys, etc.). Override."""

    def render_paused(self):
        """Draw the blank holding frame while a triggered demo waits."""
        glClear(GL_COLOR_BUFFER_BIT)

    def on_pause(self):
        """Called once at construction when the demo starts paused. Override to
        e.g. pause music that autostarted."""

    # ---- main loop ------------------------------------------------------
    def run(self):
        self.running = True
        while self.running:
            self._process_events()
            if self.paused:
                self.render_paused()
            else:
                self.step()
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
            elif event.type == MOUSEBUTTONDOWN:
                self.trigger()
            else:
                self.handle_event(event)
