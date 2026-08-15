import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame

from lib.textwall import TextWallArray, PygameTextWall
from lib.test.corpus import load_text, build_lines

WIDTH, HEIGHT = 800, 600
GREEN = (51, 255, 102)
BLUE = (102, 204, 255)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TextWall - pygame")
    clock = pygame.time.Clock()
    layout = dict(x=16, y=12, initial_screen_y=260, rows=25,
                  speed=60, loop=False, font_size=18)
    wall_a = PygameTextWall(build_lines(load_text("kaplus.txt")), surface=screen, color=GREEN, **layout)
    wall_b = PygameTextWall(build_lines(load_text("karate.txt")), surface=screen, color=BLUE, **layout)
    walls = TextWallArray()
    walls.add(wall_a, 0.0)
    walls.add(wall_b, 0.5)
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
