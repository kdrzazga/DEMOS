from demos.petscii.files.globals import Constants


class PetsciiScreen:

    def __init__(self, characters, colors, uppercase=False):
        self.characters = characters
        self.colors = colors
        self.uppercase = uppercase

    @classmethod
    def from_file(cls, path, uppercase=False):
        characters, colors = cls._parse(path)
        return cls(characters, colors, uppercase)

    @classmethod
    def _parse(cls, path):
        segments = ([], [])
        segment_index = -1
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(";"):
                    segment_index += 1
                    continue
                if not 0 <= segment_index < len(segments):
                    continue
                for token in stripped.split(","):
                    token = token.strip()
                    if token:
                        segments[segment_index].append(int(token))
        return cls._to_grid(segments[0]), cls._to_grid(segments[1])

    @staticmethod
    def _to_grid(values):
        columns = Constants.COLUMNS
        row_count = len(values) // columns
        return tuple(
            tuple(values[row * columns:(row + 1) * columns])
            for row in range(row_count)
        )
