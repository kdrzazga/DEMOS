import pygame
from pygame.locals import DOUBLEBUF, FULLSCREEN, KEYDOWN, K_ESCAPE, MOUSEBUTTONDOWN, OPENGL, QUIT
from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glViewport

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
        # the desktop resolution, read BEFORE set_mode (Info() reports the desktop
        # mode until then). In fullscreen pygame-ce keeps this native size as the GL
        # drawable while still reporting the requested size, so _fit_viewport needs
        # the real size to place the viewport instead of leaving it bottom-left.
        desktop = pygame.display.Info()
        self.desktop_size = (desktop.current_w, desktop.current_h)
        flags = 0
        if opengl:
            flags |= DOUBLEBUF | OPENGL
        if not self.windowed:
            flags |= FULLSCREEN
        pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)
        if opengl:
            self._fit_viewport()

        self.clock = pygame.time.Clock()
        self.running = False

        self.setup()
        if self.paused:
            self.on_pause()

    def _fit_viewport(self):
        """Fit a width:height-aspect viewport into the actual drawable, centred.

        pygame-ce/SDL2 fullscreen keeps the native desktop resolution rather than
        switching to the requested mode (as SDL1 did), so the drawable is larger
        than (width, height) while the default GL viewport stays at the requested
        size -- which drops everything into the bottom-left corner. Reset the
        viewport to the real drawable, letterboxed so the aspect stays correct.

        The drawable size comes from the desktop resolution captured before
        set_mode, since get_window_size()/get_surface() report the requested
        logical size for an OpenGL surface, not the physical fullscreen resolution.
        """
        if self.windowed:
            drawable_width, drawable_height = self.width, self.height
        else:
            drawable_width, drawable_height = self.desktop_size
        target_aspect = self.width / self.height
        if drawable_width / drawable_height > target_aspect:
            view_height = drawable_height
            view_width = round(view_height * target_aspect)
        else:
            view_width = drawable_width
            view_height = round(view_width / target_aspect)
        glViewport((drawable_width - view_width) // 2, (drawable_height - view_height) // 2,
                   view_width, view_height)

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
