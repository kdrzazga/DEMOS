import pygame

from demos.petscii.files.globals import Constants
from demos.petscii.files.tilt_screen import TiltScreen
from demos.petscii.files.typer import Typer


class WelcomeStage:
    """Opening screen: two captions beep-typed into the centre of the display."""

    LINE1 = "HELLO!"
    LINE2 = "Let's make some NOISE !!!"
    FONT_SIZE = 24
    LINE2_PAUSE = 15  # frames to wait after line 1 finishes before line 2 starts

    def __init__(self):
        pygame.font.init()
        self.surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))

        font = pygame.font.Font(Constants.FONT_PATH, WelcomeStage.FONT_SIZE)
        line_height = font.get_height()
        center_x = Constants.WIDTH // 2
        center_y = Constants.HEIGHT // 2
        x1 = center_x - font.size(WelcomeStage.LINE1)[0] // 2
        x2 = center_x - font.size(WelcomeStage.LINE2)[0] // 2
        y1 = center_y - line_height
        y2 = center_y + line_height

        self.typer1 = Typer(0, WelcomeStage.LINE1, self.surface, x1, y1, WelcomeStage.FONT_SIZE)
        line2_start = len(WelcomeStage.LINE1) + WelcomeStage.LINE2_PAUSE
        self.typer2 = Typer(line2_start, WelcomeStage.LINE2, self.surface, x2, y2, WelcomeStage.FONT_SIZE)

        self.screen = TiltScreen(Constants.WIDTH, Constants.HEIGHT)

    def update(self, frame):
        """Compose the captions onto the surface, beeping on each new letter."""
        self.surface.fill((0, 0, 0))
        self.typer1.type(frame, beeping=True)
        self.typer2.type(frame, beeping=True)

    def draw(self):
        self.screen.draw_flat(self.surface)
