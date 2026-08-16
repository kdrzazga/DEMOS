import os

from lib.textwall import TextWallArray, PygameTextWall
from lib.petscii_textwall import PetsciiTextWall
from lib.c64_frame import C64Frame
from lib.petscii_screen import PetsciiScreen
from lib.petscii_image import PetsciiImage
from lib.test.corpus import build_lines
from demos.petscii.files.globals import Constants

RESOURCES = os.path.join(os.path.dirname(__file__), "resources")
LARGE_TEXT = os.path.join(RESOURCES, "large-text")
PETSCII = os.path.join(RESOURCES, "petscii")


class ScreenWindingAnim:

    def __init__(self, surface, *, char_size=16, border=None, text_color=(51, 255, 102),
                 border_color=14, background_color=0, read_speed=15, fill_speed=120,
                 picture_speed=30, intro_pause=2.0, market_pause=5.0):
        self.surface = surface
        self.char_size = char_size
        self.border = border
        self.text_color = text_color
        self.background_color = background_color
        self.picture_speed = picture_speed

        market_image = self._load_image("market_in_poland.txt", background_color=0)
        bajtek_image = self._load_image("logo-bajtek.txt", background_color=1)
        top_secret_image = self._load_image("logo-top-secret.txt", background_color=15)
        secret_service_image = self._load_image("logo-secret-service.txt", background_color=2)
        secret_service_description = self._load_image("secret-service.txt", background_color=2)
        kna_image = self._load_image("kna.txt", background_color=0)
        mosaic_image = self._load_image("mosaic.txt", background_color=0)
        self.font = market_image.font(char_size)
        self.cell_width, self.cell_height = self.font.size("W")
        self.frame = self._build_frame(border_color, background_color)

        self.walls = TextWallArray()
        self.walls.add(self._build_text_wall("intro.txt", read_speed, background_color=0, font_color=self.text_color), 0.0)
        self.walls.add(self._build_text_wall("kaplus.txt", fill_speed, background_color=0, font_color=self.text_color), intro_pause)
        self.walls.add(self._build_petscii_wall(market_image), 0.0)
        self.walls.add(self._build_text_wall("karate.txt", fill_speed, background_color=0, font_color=self.text_color), market_pause)
        self.walls.add(self._build_petscii_wall(bajtek_image), 0.3)
        self.walls.add(self._build_text_wall("bajtek.txt", fill_speed, background_color=1, font_color=0), 3.0)
        self.walls.add(self._build_petscii_wall(top_secret_image), 6)
        self.walls.add(self._build_text_wall("top-secret.txt", fill_speed, background_color=15, font_color=4), 3.0)
        self.walls.add(self._build_text_wall("top-secret2.txt", fill_speed, background_color=15, font_color=0), 2.5)
        self.walls.add(self._build_text_wall("top-secret3.txt", fill_speed, background_color=15, font_color=6), 2.0)
        self.walls.add(self._build_text_wall("karate.txt", fill_speed, background_color=15, font_color=1),4)
        self.walls.add(self._build_petscii_wall(secret_service_image), 0.5)
        self.walls.add(self._build_petscii_wall(secret_service_description), 6)
        self.walls.add(self._build_text_wall("karate.txt", fill_speed, background_color=3, font_color=1),14)
        self.walls.add(self._build_petscii_wall(kna_image), 0.1)

        self.frame.set_content(self.walls)

    def update(self, dt):
        self.frame.update(dt)

    def draw(self):
        self.frame.draw()

    def _build_frame(self, border_color, background_color):
        width, height = self.surface.get_size()
        border = self.border if self.border is not None else 2 * self.cell_width
        total_width = Constants.COLUMNS * self.cell_width + 2 * border
        total_height = Constants.ROWS * self.cell_height + 2 * border
        origin = ((width - total_width) // 2, (height - total_height) // 2)
        return C64Frame(self.surface, cell_width=self.cell_width, cell_height=self.cell_height,
                        border=border, border_color=border_color,
                        background_color=background_color, origin=origin)

    def _load_image(self, name, background_color):
        screen = PetsciiScreen.from_file(os.path.join(PETSCII, name), uppercase=True,
                                         background_color=background_color)
        return PetsciiImage.from_petscii_screen(screen, char_size=self.char_size)

    def _build_text_wall(self, name, speed, background_color, font_color):
        text = self._load_text(os.path.join(LARGE_TEXT, name))
        return PygameTextWall(build_lines(text, Constants.COLUMNS), surface=self.surface,
                              font=self.font, antialias=False, color=font_color,
                              background_color=background_color,
                              x=self.frame.char_x, y=self.frame.char_y,
                              initial_screen_y=self.frame.char_y, rows=Constants.ROWS,
                              speed=speed, line_step=self.cell_height, loop=False)

    def _build_petscii_wall(self, image):
        return PetsciiTextWall(image, surface=self.surface, x=self.frame.char_x,
                               y=self.frame.char_y, rows=Constants.ROWS,
                               speed=self.picture_speed, loop=False, char_size=self.char_size,
                               background_color=image.background_color)

    @staticmethod
    def _load_text(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()
