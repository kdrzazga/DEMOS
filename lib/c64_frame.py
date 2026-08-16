from demos.petscii.files.globals import Constants


class C64Frame:

    def __init__(self, surface, *, cell_width, cell_height, columns=Constants.COLUMNS,
                 rows=Constants.ROWS, border=None, border_color=14, background_color=6,
                 origin=(0, 0)):
        self.surface = surface
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.columns = columns
        self.rows = rows
        self.border = 2 * cell_width if border is None else border
        self.border_color = border_color
        self.background_color = background_color
        self.origin_x, self.origin_y = origin
        self.content = None

    def set_content(self, content):
        self.content = content
        return self

    def set_border_color(self, index):
        self.border_color = index
        return self

    def set_background_color(self, index):
        self.background_color = index
        return self

    @property
    def char_x(self):
        return self.origin_x + self.border

    @property
    def char_y(self):
        return self.origin_y + self.border

    @property
    def char_width(self):
        return self.columns * self.cell_width

    @property
    def char_height(self):
        return self.rows * self.cell_height

    @property
    def width(self):
        return self.char_width + 2 * self.border

    @property
    def height(self):
        return self.char_height + 2 * self.border

    def update(self, dt):
        if self.content is not None:
            self.content.update(dt)

    def draw(self):
        self.surface.fill(Constants.PALETTE[self.border_color],
                          (self.origin_x, self.origin_y, self.width, self.height))
        char_rect = (self.char_x, self.char_y, self.char_width, self.char_height)
        self.surface.fill(Constants.PALETTE[self.background_color], char_rect)
        if self.content is None:
            return
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(char_rect)
        self.content.draw()
        self.surface.set_clip(previous_clip)
