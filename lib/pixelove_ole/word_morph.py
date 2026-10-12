import math

from lib.pixelove_ole.letters import LetterRow


def ease_in_out(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def phase(progress, start, end):
    return ease_in_out((progress - start) / (end - start))


class LetterMove:
    """One letter's trip between two slots (scale 0 = not in that word)."""

    def __init__(self, letter, start_x, end_x, start_scale, end_scale):
        self.letter = letter
        self.start_x = start_x
        self.end_x = end_x
        self.start_scale = start_scale
        self.end_scale = end_scale


class WordMorph:
    """Rearranges a pool of BlockLetters from one word to another, e.g. the
    lower row LOVE -> OLE: V spins away, the rest slide into their new slots,
    hopping forward when moving left and lifting up when moving right, so they
    never pass through each other (nor the gamepad / invader behind them)."""

    def __init__(self, row, letters, word, duration=1.8, hop_depth=0.9, hop_height=0.25, spin=25.0):
        self.row = row
        self.letters = letters
        self.duration = duration
        self.hop_depth = hop_depth
        self.hop_height = hop_height
        self.spin = spin
        self.moves = []
        self.elapsed = 0.0
        self.word = word
        self.snap(word)

    @property
    def animating(self):
        return bool(self.moves) and self.elapsed < self.duration

    def slots(self, word):
        """Letter -> x for `word`, taken from the row layout; letters not in the word map to None."""
        layout = LetterRow(word, self.row.center_x, self.row.center_y, self.row.z, self.row.cell_width,
                           self.row.cell_height, self.row.depth, self.row.gap, self.row.style, "")
        positions = {}
        free = list(self.letters)
        for placed in layout.build_letters():
            letter = next(candidate for candidate in free if candidate.character == placed.character)
            free.remove(letter)
            positions[letter] = placed.x
        for letter in free:
            positions[letter] = None
        return positions

    def place(self, letter, x, scale, yaw=0.0, z_offset=0.0, y_offset=0.0):
        y, z = self.row.center_y + y_offset, self.row.z + z_offset
        letter.x, letter.y, letter.z = x, y, z
        letter.home = (x, y, z)
        letter.scale = scale
        letter.yaw = yaw
        letter.visible = scale > 0.001

    def snap(self, word):
        self.word = word
        self.moves = []
        for letter, x in self.slots(word).items():
            self.place(letter, letter.x if x is None else x, 1.0 if x is not None else 0.0)

    def morph_to(self, word):
        if word == self.word:
            return
        current = {letter: letter.x for letter in self.letters}
        target = self.slots(word)
        self.moves = [LetterMove(letter, current[letter], current[letter] if target[letter] is None else target[letter],
                                 letter.scale, 0.0 if target[letter] is None else 1.0)
                      for letter in self.letters]
        self.word = word
        self.elapsed = 0.0

    def update(self, delta_seconds):
        if not self.moves:
            return
        self.elapsed += delta_seconds
        progress = min(1.0, self.elapsed / self.duration)
        for move in self.moves:
            if move.end_scale < move.start_scale:
                # Leaving: spin away and shrink before the others start moving in.
                vanish = phase(progress, 0.0, 0.45)
                scale = move.start_scale * (1.0 - vanish)
                self.place(move.letter, move.start_x, scale, yaw=540.0 * vanish, y_offset=-0.4 * vanish)
            elif move.end_scale > move.start_scale:
                # Arriving: grow in once the others have made room.
                appear = phase(progress, 0.55, 1.0)
                self.place(move.letter, move.end_x, appear, yaw=-540.0 * (1.0 - appear))
            else:
                travel = phase(progress, 0.3, 1.0)
                hop = math.sin(math.pi * travel)
                direction = -1.0 if move.end_x < move.start_x else 1.0
                if move.end_x == move.start_x:
                    hop = direction = 0.0
                x = move.start_x + (move.end_x - move.start_x) * travel
                moving_left = direction < 0
                self.place(move.letter, x, 1.0, yaw=self.spin * hop * direction,
                           z_offset=self.hop_depth * hop if moving_left else 0.0,
                           y_offset=self.hop_height * hop * (1.0 if moving_left else 2.5))
        if progress >= 1.0:
            self.moves = []
