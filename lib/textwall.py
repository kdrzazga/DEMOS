import arcade
import pygame


class TextWall:

    def __init__(self, lines=None, *, speed=20, x=16, y=12,
                 initial_screen_y=0, rows=24, color=(51, 255, 102),
                 font_size=18, line_step=None, font_name="Courier New",
                 loop=True):
        self.lines = tuple(lines) if lines else ()
        self.cursor = 0
        self.loop = loop
        self.progress = 0.0
        self.speed = speed
        self.x = x
        self.y = y
        self.initial_screen_y = initial_screen_y
        self.rows = rows
        self.color = color
        self.font_size = font_size
        self.font_name = font_name
        self.line_step = line_step if line_step is not None else font_size * 1.5
        pad = round((self.initial_screen_y - self.y) / self.line_step)
        self._pad_lines = max(0, min(pad, self.rows - 1))
        self.visible = self._fresh_buffer()

    def draw_line(self, text, x, y):
        raise NotImplementedError("TextWall subclasses must implement draw_line()")

    def draw_lines(self, lines, x, y_top):
        y = y_top
        for line in lines:
            if line:
                self.draw_line(line, x, y)
            y += self.line_step

    def draw(self):
        self.draw_lines(self.visible, self.x, self.y)

    def _fresh_buffer(self):
        return ["" for _ in range(self._pad_lines)]

    def set_lines(self, lines):
        self.lines = tuple(lines) if lines else ()
        self.cursor = 0
        return self

    def reset(self):
        self.progress = 0.0
        self.cursor = 0
        self.visible = self._fresh_buffer()
        return self

    def tick(self, dt):
        if not self.lines:
            return []
        self.progress += dt * self.speed
        revealed = []
        while self.progress >= 1:
            self.progress -= 1
            line = self._next_line()
            if line is None:
                self.progress = 0
                break
            revealed.append(line)
        return revealed

    def write(self, dt):
        for line in self.tick(dt):
            self._push_line(line)

    def _next_line(self):
        if self.cursor >= len(self.lines):
            if not self.loop:
                return None
            self.cursor = 0
        line = self.lines[self.cursor]
        self.cursor += 1
        return line

    def is_finished(self):
        return (not self.loop) and 0 < len(self.lines) <= self.cursor

    def _push_line(self, line):
        self.visible.append(line)
        if len(self.visible) > self.rows:
            self.visible.pop(0)


class TextWallArray:

    def __init__(self):
        self.walls = []
        self.intervals = []
        self._index = 0
        self._phase = "waiting"
        self._wait_remaining = 0.0
        self._started = False
        self.buffer = []

    def add(self, wall, interval=0.0):
        self.walls.append(wall)
        self.intervals.append(interval)
        return self

    @property
    def _band_top(self):
        return self.walls[0].y

    @property
    def _rows(self):
        return self.walls[0].rows

    @property
    def _line_step(self):
        return self.walls[0].line_step

    def _add_line(self, text, wall_index):
        self.buffer.append((text, wall_index))
        if len(self.buffer) > self._rows:
            self.buffer.pop(0)

    def update(self, dt):
        if not self.walls:
            return

        if not self._started:
            self._started = True
            self._index = 0
            self._wait_remaining = self.intervals[0] if self.intervals else 0.0
            self._phase = "waiting" if self._wait_remaining > 0 else "animating"
            for _ in range(getattr(self.walls[0], "_pad_lines", 0)):
                self._add_line("", 0)

        if self._phase == "done":
            return

        if self._phase == "waiting":
            self._wait_remaining -= dt
            if self._wait_remaining > 0:
                return
            self._phase = "animating"

        if self._phase == "animating":
            wall = self.walls[self._index]
            for line in wall.tick(dt):
                self._add_line(line, self._index)

            if wall.is_finished():
                if self._index + 1 < len(self.walls):
                    self._index += 1
                    self._wait_remaining = self.intervals[self._index]
                    self._phase = "waiting" if self._wait_remaining > 0 else "animating"
                else:
                    self._phase = "done"

    def draw(self):
        band_top = self._band_top
        step = self._line_step
        offset = 0
        for w, wall in enumerate(self.walls):
            slice_lines = [text for (text, wi) in self.buffer if wi == w]
            if not slice_lines:
                continue
            wall.draw_lines(slice_lines, wall.x, band_top + offset * step)
            offset += len(slice_lines)

    def reset(self):
        self._started = False
        self._index = 0
        self._phase = "waiting"
        self._wait_remaining = 0.0
        self.buffer = []
        for wall in self.walls:
            wall.reset()
        return self


class ArcadeTextWall(TextWall):

    def __init__(self, lines=None, *, screen_height, **kwargs):
        super().__init__(lines, **kwargs)
        self.screen_height = screen_height
        self._texts = []

    def _rgba(self):
        return self.color if len(self.color) == 4 else (*self.color, 255)

    def draw_lines(self, lines, x, y_top):
        color = self._rgba()
        step = self.line_step
        for i, line in enumerate(lines):
            if i >= len(self._texts):
                self._texts.append(arcade.Text(
                    "", x=0, y=0, color=color,
                    font_size=self.font_size, font_name=self.font_name,
                    anchor_x="left", anchor_y="top",
                ))
            text_obj = self._texts[i]
            text_obj.text = line
            text_obj.x = x
            text_obj.y = self.screen_height - (y_top + i * step)
            text_obj.color = color
            if line:
                text_obj.draw()

    def draw_line(self, text, x, y):
        arcade.Text(
            text, x=x, y=self.screen_height - y, color=self._rgba(),
            font_size=self.font_size, font_name=self.font_name,
            anchor_x="left", anchor_y="top",
        ).draw()


class PygameTextWall(TextWall):

    def __init__(self, lines=None, *, surface, font=None, antialias=True, **kwargs):
        super().__init__(lines, **kwargs)
        self.surface = surface
        self.antialias = antialias
        if font is None:
            font = pygame.font.SysFont(self.font_name, self.font_size)
        self.font = font

    def draw_line(self, text, x, y):
        image = self.font.render(text, self.antialias, self.color)
        self.surface.blit(image, (x, y))
