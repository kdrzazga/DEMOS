import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame

from lib.textwall import TextWallArray, PygameTextWall
from lib.petscii_textwall import PetsciiTextWall
from lib.c64_frame import C64Frame
from lib.petscii_screen import PetsciiScreen
from lib.petscii_image import PetsciiImage
from lib.test.corpus import load_text, build_lines

WIDTH, HEIGHT = 800, 600
GREEN = (51, 255, 102)
CHAR_SIZE = 16
BACKGROUND_CYCLE = (6, 0, 11, 14)
RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "demos", "petscii",
                            "files", "resources")
PETSCII_PATH = os.path.join(RESOURCE_PATH, "petscii")
LARGE_TEXT_PATH = os.path.join(RESOURCE_PATH, "large-text")

def build_frame(screen):
    petscii_screen = PetsciiScreen.from_file(PETSCII_PATH + "\\petscii.txt", uppercase=True, background_color=6)
    petscii_image = PetsciiImage.from_petscii_screen(petscii_screen, char_size=CHAR_SIZE)
    c64_font = petscii_image.font(CHAR_SIZE)
    cell_width, cell_height = c64_font.size("W")

    border = 2 * cell_width
    total_width = 40 * cell_width + 2 * border
    total_height = 25 * cell_height + 2 * border
    origin = ((WIDTH - total_width) // 2, (HEIGHT - total_height) // 2)
    frame = C64Frame(screen, cell_width=cell_width, cell_height=cell_height, border=border,
                     border_color=14, background_color=6, origin=origin)

    text_wall = PygameTextWall(build_lines(load_text(LARGE_TEXT_PATH + "\\kaplus.txt"), 40), surface=screen,
                               font=c64_font, antialias=False, color=GREEN,
                               x=frame.char_x, y=frame.char_y, initial_screen_y=frame.char_y,
                               rows=25, speed=20, line_step=cell_height, loop=False)
    petscii_wall = PetsciiTextWall(petscii_image, surface=screen, x=frame.char_x,
                                   y=frame.char_y, rows=25, speed=20, loop=False,
                                   char_size=CHAR_SIZE)

    walls = TextWallArray()
    walls.add(text_wall, 0.0)
    walls.add(petscii_wall, 0.5)
    frame.set_content(walls)
    return frame


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("C64 screen - petscii")
    clock = pygame.time.Clock()

    frame = build_frame(screen)

    elapsed = 0.0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        frame.set_border_color(1 + int(elapsed * 5) % 15)
        frame.set_background_color(BACKGROUND_CYCLE[int(elapsed) % len(BACKGROUND_CYCLE)])

        screen.fill((0, 0, 0))
        frame.update(dt)
        frame.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
