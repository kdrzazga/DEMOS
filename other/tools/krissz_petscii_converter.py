import re

COLUMNS = 40


def parse_numbers(text):
    numbers = []
    for line in text.splitlines():
        content = line.split(";", 1)[0]
        for token in re.findall(r"\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|\d+", content):
            if token.startswith("$"):
                numbers.append(int(token[1:], 16))
            elif token[:2] in ("0x", "0X"):
                numbers.append(int(token, 16))
            else:
                numbers.append(int(token))
    return numbers


def screen_to_petscii(code):
    if code < 32:
        return code + 64
    if code < 64:
        return code
    if code < 96:
        return code + 32
    return code + 64


def to_grid(values, columns):
    return tuple(
        tuple(values[start:start + columns])
        for start in range(0, len(values), columns)
    )


def grid_to_text(grid):
    rows = []
    for row in grid:
        rows.append("(" + ", ".join(str(value) for value in row) + "),")
    return "\n".join(rows)


def normalize_class_name(text):
    words = re.findall(r"[A-Za-z0-9]+", text)
    name = "".join(word[:1].upper() + word[1:] for word in words)
    if not name:
        return "PetsciiImageClass"
    if name[0].isdigit():
        return "_" + name
    return name


def to_file_name(class_name):
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
    return snake + ".py"


class DesiredClass:

    def __init__(self, name, chars, colors, reversed):
        self.name = name
        self.chars = chars
        self.colors = colors
        self.reversed = reversed

    def trimmed(self, last_row, last_column):
        return DesiredClass(
            self.name,
            self._crop(self.chars, last_row, last_column),
            self._crop(self.colors, last_row, last_column),
            self._crop(self.reversed, last_row, last_column),
        )

    @staticmethod
    def _crop(grid, last_row, last_column):
        return tuple(row[:last_column] for row in grid[:last_row])

    def render_source(self):
        blocks = [
            "from lib.petscii_image import PetsciiImage",
            "",
            "",
            f"class {self.name}(PetsciiImage):",
            "",
            self._format_attribute("chars", self.chars),
            "",
            self._format_attribute("reversed", self.reversed),
            "",
            self._format_attribute("colors", self.colors),
            "",
        ]
        return "\n".join(blocks)

    def create_class(self, path):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.render_source())

    def _format_attribute(self, name, grid):
        indented = "\n".join("        " + line for line in grid_to_text(grid).splitlines())
        return f"    {name} = (\n{indented}\n    )"


class Converter:

    def __init__(self, input_character_data, input_color_data, dest_class_name, columns=COLUMNS):
        self.input_character_data = input_character_data
        self.input_color_data = input_color_data
        self.dest_class_name = dest_class_name
        self.columns = columns
        self.desired_class = None

    def convert(self):
        character_codes = parse_numbers(self.input_character_data)
        color_codes = parse_numbers(self.input_color_data)
        self._validate(character_codes, color_codes)
        chars = []
        reversed_cells = []
        for code in character_codes:
            reversed_cells.append(1 if code >= 128 else 0)
            chars.append(screen_to_petscii(code & 0x7F))
        colors = [code & 0x0F for code in color_codes]
        self.desired_class = DesiredClass(
            normalize_class_name(self.dest_class_name),
            to_grid(chars, self.columns),
            to_grid(colors, self.columns),
            to_grid(reversed_cells, self.columns),
        )
        return self.desired_class

    def _validate(self, character_codes, color_codes):
        if not character_codes:
            raise ValueError("Input Char Data has no numbers.")
        if not color_codes:
            raise ValueError("Input Color Data has no numbers.")
        if len(character_codes) % self.columns != 0:
            raise ValueError(
                f"Input Char Data has {len(character_codes)} values, not a multiple of {self.columns}."
            )
        if len(color_codes) != len(character_codes):
            raise ValueError(
                f"Input Color Data has {len(color_codes)} values but Input Char Data has {len(character_codes)}."
            )
