import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame

from lib.textwall import TextWallArray, PygameTextWall
from lib.petscii_textwall import PetsciiTextWall
from lib.test.corpus import load_text, build_lines
from demos.petscii.files.petscii_screen import PetsciiScreen
from demos.petscii.files.petscii_image import PetsciiImage

WIDTH, HEIGHT = 800, 600
GREEN = (51, 255, 102)
CHAR_SIZE = 16
PETSCII_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "petscii.txt")


def build_walls(screen):
    text_wall = PygameTextWall(build_lines(load_text("kaplus.txt")), surface=screen,
                               color=GREEN, x=16, y=12, initial_screen_y=260,
                               rows=25, speed=20, loop=False)

    petscii_screen = PetsciiScreen.from_file(PETSCII_PATH, uppercase=False, background_color=2)
    petscii_image = PetsciiImage.from_petscii_screen(petscii_screen, char_size=CHAR_SIZE)
    picture_width = petscii_image.font(CHAR_SIZE).size("W")[0] * 40
    petscii_wall = PetsciiTextWall(petscii_image, surface=screen,
                                   x=(WIDTH - picture_width) // 2, y=12,
                                   rows=25, speed=20, loop=False, char_size=CHAR_SIZE)

    walls = TextWallArray()
    walls.add(text_wall, 0.0)
    walls.add(petscii_wall, 0.5)
    return walls


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TextWall - petscii")
    clock = pygame.time.Clock()

    walls = build_walls(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        screen.fill((0, 0, 0))
        walls.update(dt)
        walls.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
