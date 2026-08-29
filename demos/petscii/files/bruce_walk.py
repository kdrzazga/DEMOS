from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.bruce_lee import BruceLee


class BruceWalk:
    """Walks a BruceLee sprite left-to-right across a 40-column screen face.

    The routine: stand for a moment, walk (run1/run2 alternating) rightward,
    switch to a kick through a band of the screen, walk again, and stop once it
    reaches the right border. Call :meth:`update` once per frame and stamp
    :attr:`sprite` onto a screen with ``show_bruce_pose``; :attr:`at_border`
    turns True once the walk has finished.
    """

    STAND = 0
    WALK_TO_KICK = 1
    KICK = 2
    WALK_TO_BORDER = 3
    DONE = 4

    def __init__(self, char_size, row, start_column=2):
        self.sprite = BruceLee(char_size)
        self.row = row
        self.column = float(start_column)

        # tunables -- kept on the instance so the walk is easy to nudge
        self.walk_speed = 0.3                       # columns advanced per frame
        self.step_frames = 5                        # frames per run1/run2 leg
        self.stand_frames = int(Constants.FPS)      # stand this long before setting off
        self.sprite_width = 6                        # kept clear of the right edge
        self.kick_start_column = 2 / 3 * Constants.COLUMNS
        self.kick_end_column = 3 / 4 * Constants.COLUMNS
        self.border_column = Constants.COLUMNS - self.sprite_width

        self.phase = BruceWalk.STAND
        self.timer = 0
        self._stamp("stand")

    @property
    def at_border(self):
        return self.phase == BruceWalk.DONE

    def update(self):
        if self.phase == BruceWalk.STAND:
            self._stamp("stand")
            self.timer += 1
            if self.timer >= self.stand_frames:
                self.phase = BruceWalk.WALK_TO_KICK
                self.timer = 0
        elif self.phase == BruceWalk.WALK_TO_KICK:
            self._walk()
            if self.column >= self.kick_start_column:
                self.phase = BruceWalk.KICK
        elif self.phase == BruceWalk.KICK:
            self._advance()
            self._stamp("kick")
            if self.column >= self.kick_end_column:
                self.phase = BruceWalk.WALK_TO_BORDER
        elif self.phase == BruceWalk.WALK_TO_BORDER:
            self._walk()
            if self.column >= self.border_column:
                self.phase = BruceWalk.DONE
                self._stamp("stand")

    def _walk(self):
        """Advance a step and show the next leg of the run cycle."""
        self._advance()
        leg = (self.timer // self.step_frames) % 2
        self._stamp("run1" if leg == 0 else "run2")
        self.timer += 1

    def _advance(self):
        self.column = min(self.border_column, self.column + self.walk_speed)

    def _stamp(self, pose):
        """Place the sprite at the current cell and paste the given pose there."""
        self.sprite.origin = (self.row, int(self.column))
        getattr(self.sprite, pose)()
