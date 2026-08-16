import os
import sys

import pygame

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _ROOT)

from demos.petscii.files.screen_winding_anim import ScreenWindingAnim


WIDTH, HEIGHT = 800, 600


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Screen Winding Anim")
    clock = pygame.time.Clock()

    anim = ScreenWindingAnim(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.fill((0, 0, 0))
        anim.update(dt)
        anim.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
