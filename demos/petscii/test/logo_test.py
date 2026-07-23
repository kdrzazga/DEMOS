import os
import sys

import pygame

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from demos.petscii.files.kna_logo import KnaLogo


def main():
    pygame.init()
    image = KnaLogo()
    screen = pygame.display.set_mode(image.size())
    pygame.display.set_caption("K&A PLUS logo")
    clock = pygame.time.Clock()

    image.render(screen)
    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
