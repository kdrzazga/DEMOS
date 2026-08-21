from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.bruce_lee import BruceLee


class BruceSprite(BruceLee):
    """A single Bruce Lee pose used as a free-standing, movable sprite -- as opposed
    to the full-screen BruceLee stages. He performs a fixed routine: drops in from
    above the top edge in the jump pose, lands on the bottom, runs a few characters
    left, then runs back to the right, and finishes with a kick. run1/run2 alternate
    to animate his legs while he moves.

    The sprite owns its own screen-space position and animation state; a screen just
    calls start_fall() once, then update() and render_at_origin() each frame."""

    def __init__(self, char_size):
        super().__init__(char_size)
        self.jump()

        # screen-space position (pixels) and drop-in physics
        self.origin_px = (0.0, 0.0)
        self.velocity = 0.0
        self.rest_y = 0.0
        self.landed = False

        # after landing: run left, run right, then kick (final)
        self.action = None          # None | 'run_left' | 'run_right' | 'done'
        self.action_frame = 0
        self.run_target_x = 0.0
        self.run_pose = 2           # last running frame shown (1 or 2)

        # tunables
        self.gravity = Constants.HEIGHT * 0.006   # drops in over ~0.8s at 25 fps
        self.run_left_columns = 4
        self.run_right_columns = 8
        self.run_speed_fraction = 0.3   # cell widths moved per frame
        self.run_pose_frames = 4        # frames between run1/run2 swaps

    def cell_size(self):
        return self.font(self.char_size).size("W")

    def bounds(self):
        """(top_row, bottom_row, left_column, right_column) of the non-blank cells."""
        cells = [(row, column)
                 for row in range(Constants.ROWS)
                 for column in range(Constants.COLUMNS)
                 if not self.is_blank(row, column)]
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        return min(rows), max(rows), min(columns), max(columns)

    def start_fall(self):
        """Drop in from above the top edge, horizontally centred, so his feet land
        on the bottom border of the screen face at his own char size."""
        self.jump()
        cell_width, cell_height = self.cell_size()
        _, bottom_row, left_column, right_column = self.bounds()
        sprite_columns = right_column - left_column + 1
        centred_x = (Constants.WIDTH - sprite_columns * cell_width) // 2
        origin_x = centred_x - left_column * cell_width
        self.rest_y = Constants.HEIGHT - (bottom_row + 1) * cell_height
        self.origin_px = (origin_x, -(bottom_row + 1) * cell_height)
        self.velocity = 0.0
        self.landed = False
        self.action = None

    def update(self):
        """Advance one frame: fall, then run left / right, then kick."""
        cell_width, cell_height = self.cell_size()
        if not self.landed:
            self._fall(cell_width)
        elif self.action not in (None, "done"):
            self._run(cell_width, cell_height)

    def render_at_origin(self, surface):
        origin_x, origin_y = self.origin_px
        self.render(surface, transparent_space=True, origin=(int(origin_x), int(origin_y)))

    def _fall(self, cell_width):
        """Drop under gravity until his feet reach the rest line, then start running."""
        origin_x, origin_y = self.origin_px
        self.velocity += self.gravity
        origin_y += self.velocity
        if origin_y >= self.rest_y:
            origin_y = self.rest_y
            self.landed = True
            self.action = "run_left"
            self.action_frame = 0
            self.run_target_x = origin_x - self.run_left_columns * cell_width
            self._swap_running_pose()
        self.origin_px = (origin_x, origin_y)

    def _run(self, cell_width, cell_height):
        """Slide toward the current phase's target, animating the legs; when he
        arrives, move on to the next phase (right run, then the finishing kick)."""
        origin_x, origin_y = self.origin_px
        speed = max(1.0, cell_width * self.run_speed_fraction)
        if origin_x < self.run_target_x:
            origin_x = min(origin_x + speed, self.run_target_x)
        else:
            origin_x = max(origin_x - speed, self.run_target_x)
        self.origin_px = (origin_x, origin_y)

        self.action_frame += 1
        if self.action_frame % self.run_pose_frames == 0:
            self._swap_running_pose()

        if origin_x == self.run_target_x:
            self._advance_action(cell_width, cell_height)

    def _advance_action(self, cell_width, cell_height):
        """run_left -> run_right -> kick (final)."""
        if self.action == "run_left":
            self.action = "run_right"
            self.action_frame = 0
            self.run_target_x = self.origin_px[0] + self.run_right_columns * cell_width
        elif self.action == "run_right":
            self.action = "done"
            self.kick()
            # the kick pose is one row shorter than the run poses; drop the origin so
            # his standing foot still rests on the bottom edge
            _, bottom_row, _, _ = self.bounds()
            origin_x, _ = self.origin_px
            self.origin_px = (origin_x, Constants.HEIGHT - (bottom_row + 1) * cell_height)

    def _swap_running_pose(self):
        """Alternate the two running frames to animate Bruce's legs."""
        if self.run_pose == 1:
            self.run2()
            self.run_pose = 2
        else:
            self.run1()
            self.run_pose = 1
