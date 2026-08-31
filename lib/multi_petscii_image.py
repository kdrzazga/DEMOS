class MultiPetsciiImage:
    """Several PetsciiImage instances laid out side by side, left to right, as one
    picture. Each may be a different size; render() stamps them adjacent."""

    def __init__(self, images=()):
        self.images = images

    def size(self):
        total_width = 0
        max_height = 0
        for image in self.images:
            cell_width, cell_height = image.font(image.char_size).size("W")
            total_width += len(image.chars[0]) * cell_width
            max_height = max(max_height, len(image.chars) * cell_height)
        return total_width, max_height

    def render(self, surface, transparent_space=False, origin=(0, 0)):
        x, y = origin
        for image in self.images:
            rows = len(image.chars)
            columns = len(image.chars[0])
            cell_size = image.font(image.char_size).size("W")
            for row in range(rows):
                for column in range(columns):
                    if transparent_space and image.is_blank(row, column):
                        continue
                    image.draw_cell(surface, image.char_size, cell_size, row, column, (x, y))
            x += columns * cell_size[0]
