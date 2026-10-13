"""Walk around the empty entrance hall model.

Run from the DEMOS folder:  python -m demos.pixeloveole3.hall_preview

    mouse drag   look around
    W/S, A/D     walk forward/back, strafe      Q/E  down/up
    SPACE        back to the photo viewpoint
    ESC          quit
"""
import math
import os
import sys

import pygame
from pygame.locals import (DOUBLEBUF, K_ESCAPE, K_SPACE, K_a, K_d, K_e, K_q, K_s, K_w, KEYDOWN, MOUSEBUTTONDOWN,
                           MOUSEBUTTONUP, MOUSEMOTION, OPENGL, QUIT)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.pixeloveole3.hall_scene import HallScene


class HallPreview:

    def __init__(self, width=1280, height=720, fps=60, walk_speed=2.5):
        self.width = width
        self.height = height
        self.fps = fps
        self.walk_speed = walk_speed
        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Pixelove Ole 3 - hall")
        self.clock = pygame.time.Clock()
        self.scene = HallScene(width, height)
        self.dragging = False
        self.reset_view()

    def reset_view(self):
        eye, target = self.scene.photo_eye, self.scene.photo_target
        self.eye = list(eye)
        dx, dy, dz = (target[axis] - eye[axis] for axis in range(3))
        self.heading = math.atan2(dx, -dz)
        self.tilt = math.atan2(dy, math.hypot(dx, dz))

    def look_direction(self):
        return (math.sin(self.heading) * math.cos(self.tilt), math.sin(self.tilt),
                -math.cos(self.heading) * math.cos(self.tilt))

    def handle(self, event):
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            return False
        if event.type == KEYDOWN and event.key == K_SPACE:
            self.reset_view()
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            self.heading += event.rel[0] * 0.005
            self.tilt = max(-1.4, min(1.4, self.tilt - event.rel[1] * 0.005))
        return True

    def walk(self, seconds):
        keys = pygame.key.get_pressed()
        step = self.walk_speed * seconds
        forward = (math.sin(self.heading), -math.cos(self.heading))
        sideways = (math.cos(self.heading), math.sin(self.heading))
        ahead = keys[K_w] - keys[K_s]
        aside = keys[K_d] - keys[K_a]
        self.eye[0] += (forward[0] * ahead + sideways[0] * aside) * step
        self.eye[2] += (forward[1] * ahead + sideways[1] * aside) * step
        self.eye[1] += (keys[K_e] - keys[K_q]) * step

    def run(self):
        running = True
        elapsed = 0.0
        while running:
            seconds = self.clock.tick(self.fps) / 1000.0
            elapsed += seconds
            for event in pygame.event.get():
                running = self.handle(event) and running
            self.walk(seconds)
            look = self.look_direction()
            target = tuple(self.eye[axis] + look[axis] for axis in range(3))
            self.scene.render(elapsed, (tuple(self.eye), target))
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    HallPreview().run()
