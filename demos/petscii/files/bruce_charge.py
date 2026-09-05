class BruceCharge:
    """Bruce runs a few cells, then flies a kick across more cells, straight at
    Yamo -- the close of the fight on the central screen.

    It drives an existing BruceLee sprite (the one already stamped on the screen)
    rather than owning its own: each frame it advances the sprite's column and
    swaps its pose, starting from wherever the sprite currently sits. :attr:`finished`
    turns True the moment the flying kick lands on the target cell, which is
    ``start_column + run_cells + kick_cells`` -- right next to Yamo.
    """

    RUN = 0
    KICK = 1
    DONE = 2

    def __init__(self, sprite, run_cells=7, kick_cells=10,
                 run_speed=0.3, kick_speed=0.6, step_frames=5):
        self.sprite = sprite
        self.row, start_column = sprite.origin
        self.column = float(start_column)
        self.run_end_column = start_column + run_cells
        self.kick_end_column = start_column + run_cells + kick_cells
        self.run_speed = run_speed
        self.kick_speed = kick_speed          # the flying kick covers ground faster
        self.step_frames = step_frames        # frames per run1/run2 leg
        self.phase = BruceCharge.RUN
        self.timer = 0

    @property
    def finished(self):
        """True once the flying kick has landed on the target cell next to Yamo."""
        return self.phase == BruceCharge.DONE

    def update(self):
        if self.phase == BruceCharge.RUN:
            self.column = min(self.run_end_column, self.column + self.run_speed)
            leg = (self.timer // self.step_frames) % 2
            self._stamp("run1" if leg == 0 else "run2")
            self.timer += 1
            if self.column >= self.run_end_column:
                self.phase = BruceCharge.KICK
        elif self.phase == BruceCharge.KICK:
            self.column = min(self.kick_end_column, self.column + self.kick_speed)
            self._stamp("kick")
            if self.column >= self.kick_end_column:
                self.phase = BruceCharge.DONE

    def _stamp(self, pose):
        """Place the sprite at the current cell and paste the given pose there."""
        self.sprite.origin = (self.row, int(self.column))
        getattr(self.sprite, pose)()
