import os
import sys

LIB_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(LIB_DIRECTORY, "root-effect"))

import pygame

from sine_roots import SineRootGrowth

WINDOW_SIZE = (1280, 720)
FPS = 60
FAST_FORWARD = 10.0


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()
    roots = SineRootGrowth(*WINDOW_SIZE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                roots.restart()

        delta_seconds = clock.tick(FPS) / 1000.0
        if pygame.key.get_pressed()[pygame.K_f]:
            delta_seconds *= FAST_FORWARD
        roots.update(delta_seconds)
        roots.draw(screen)
        pygame.display.flip()
        pygame.display.set_caption(f"Sine roots - {roots.elapsed_seconds:.0f} s, {len(roots.roots)} tips, "
                                   f"{clock.get_fps():.0f} fps - hold F fast-forward, SPACE restart, ESC quit")

    pygame.quit()


if __name__ == "__main__":
    main()
