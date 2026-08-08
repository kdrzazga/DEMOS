from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii_image import PetsciiImage


class BruceLee(PetsciiImage):
    """An empty 40x25 picture that stamps one Bruce Lee pose over itself.

    Each pose method (stand / run1 / run2 / kick) clears the picture and pastes
    its hardcoded sprite at self.origin -- the top-left cell Bruce is drawn from.
    """

    def __init__(self, char_size):
        super().__init__(char_size)
        self.origin = (0, 0)  # (row, column) top-left corner Bruce is drawn from
        self.chars = self.blank(Constants.SPACE)
        self.reversed = self.blank(0)
        self.colors = self.blank(0)

    def blank(self, value):
        return [[value] * Constants.COLUMNS for _ in range(Constants.ROWS)]

    def stand(self):
        self.paste(
            (  # chars
                (32, 175, 32, 32, 32),
                (167, 164, 32, 32, 32),
                (110, 160, 109, 32, 32),
                (109, 164, 32, 183, 190),
                (32, 32, 188, 164, 32),
                (32, 181, 181, 181, 32),
                (32, 188, 181, 188, 32),
            ),
            (  # reversed
                (0, 0, 0, 0, 0),
                (0, 1, 0, 0, 0),
                (0, 1, 0, 0, 0),
                (0, 1, 0, 0, 0),
                (0, 1, 1, 1, 0),
                (0, 0, 0, 0, 0),
                (0, 1, 0, 1, 0),
            ),
            (  # colors
                (14, 0, 10, 10, 10),
                (0, 7, 11, 11, 10),
                (7, 7, 7, 11, 0),
                (7, 7, 11, 7, 0),
                (14, 0, 0, 11, 10),
                (10, 0, 11, 0, 10),
                (10, 0, 11, 0, 7),
            ))

    def run1(self):
        self.paste(
            (  # chars
                (32, 32, 175, 32, 160),
                (32, 167, 164, 32, 160),
                (32, 110, 32, 32, 32),
                (170, 32, 160, 187, 32),
                (188, 32, 160, 188, 164),
                (32, 32, 161, 181, 181),
                (32, 110, 32, 181, 188),
            ),
            (  # reversed
                (0, 0, 0, 0, 0),
                (0, 0, 1, 0, 0),
                (0, 0, 1, 0, 0),
                (0, 0, 1, 0, 0),
                (0, 0, 1, 1, 1),
                (0, 0, 0, 0, 0),
                (0, 0, 0, 0, 1),
            ),
            (  # colors
                (10, 14, 0, 10, 1),
                (10, 0, 7, 10, 1),
                (7, 7, 7, 7, 10),
                (7, 10, 7, 0, 10),
                (0, 10, 0, 0, 11),
                (10, 0, 0, 11, 0),
                (0, 0, 10, 11, 0),
            ))

    def run2(self):
        self.paste(
            (  # chars
                (32, 32, 175, 160, 32),
                (32, 167, 164, 160, 32),
                (32, 169, 169, 32, 32),
                (32, 160, 32, 32, 32),
                (32, 160, 32, 164, 32),
                (32, 161, 180, 32, 32),
                (110, 110, 181, 32, 32),
            ),
            (  # reversed
                (0, 0, 0, 0, 0),
                (0, 0, 1, 0, 0),
                (0, 1, 0, 0, 0),
                (0, 1, 0, 0, 0),
                (0, 1, 0, 1, 0),
                (0, 0, 0, 0, 0),
                (0, 0, 0, 0, 0),
            ),
            (  # colors
                (10, 14, 0, 1, 10),
                (10, 0, 7, 1, 10),
                (7, 7, 7, 10, 7),
                (10, 7, 7, 10, 0),
                (10, 0, 0, 11, 0),
                (0, 0, 0, 0, 0),
                (0, 0, 11, 0, 0),
            ))

    def kick(self):
        self.paste(
            (  # chars
                (32, 175, 32, 32, 32, 32, 32, 32),
                (167, 160, 175, 175, 175, 187, 32, 32),
                (32, 110, 160, 127, 32, 32, 32, 32),
                (32, 109, 127, 32, 184, 184, 185, 184),
                (32, 32, 190, 111, 164, 32, 32, 32),
                (32, 32, 32, 184, 184, 184, 32, 32),
            ),
            (  # reversed
                (0, 0, 0, 0, 0, 0, 0, 0),
                (0, 1, 0, 0, 0, 0, 0, 0),
                (0, 0, 1, 1, 0, 0, 0, 0),
                (0, 0, 0, 1, 0, 0, 1, 0),
                (0, 0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 0, 0, 0, 0),
            ),
            (  # colors
                (14, 0, 10, 10, 10, 5, 5, 5),
                (0, 7, 7, 7, 7, 0, 10, 10),
                (14, 7, 7, 7, 10, 10, 10, 10),
                (14, 7, 7, 0, 0, 0, 0, 0),
                (14, 14, 0, 0, 0, 10, 10, 10),
                (14, 14, 14, 0, 0, 0, 10, 10),
            ))

    def paste(self, chars, reverse, colors):
        self.chars = self.blank(Constants.SPACE)
        self.reversed = self.blank(0)
        self.colors = self.blank(0)
        row0, column0 = self.origin
        for delta_row, line in enumerate(chars):
            for delta_column, code in enumerate(line):
                self.chars[row0 + delta_row][column0 + delta_column] = code
        for delta_row, line in enumerate(reverse):
            for delta_column, value in enumerate(line):
                self.reversed[row0 + delta_row][column0 + delta_column] = value
        for delta_row, line in enumerate(colors):
            for delta_column, value in enumerate(line):
                self.colors[row0 + delta_row][column0 + delta_column] = value
