import math
from time import time
import random

import arcade


class Dot:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.speed = 0.0
        self.size = 1
        self.y = self.width / 2
        self.x = self.height / 2
        self.reset()

    def reset(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(30, min(self.width, self.height))
        self.x = self.width / 2 + math.cos(angle) * radius
        self.y = self.height / 2 + math.sin(angle) * radius
        self.size = 1
        self.speed = 0.0

    def update(self):
        dx = (self.width / 2) - self.x
        dy = (self.height / 2) - self.y
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
        acceleration = 0.1
        self.speed += acceleration
        self.x += dx * self.speed
        self.y += dy * self.speed
        if distance < 10:
            self.reset()


class TunnelEffect:
    def __init__(self, enlarge_delay: int, screen_width:int, screen_height:int, color:arcade.color):
        self.color = color
        self.width = screen_width
        self.height = screen_height
        NUM_DOTS = 400
        self.dots = [Dot(screen_width, screen_height) for _ in range(NUM_DOTS)]
        self.dot_size = 1
        self.enlarge_time = time() + enlarge_delay

    def draw(self):
        for dot in self.dots:
            arcade.draw_circle_filled(dot.x, dot.y, self.dot_size, self.color)

    def update(self):
        #print(self.enlarge_time, time())
        if self.enlarge_time < time() and self.dot_size < 0.12*self.width:
            self.dot_size += 0.05 + 0.01*self.dot_size**1.75

        for dot in self.dots:
            dot.update()

    def new_dot(self, speed):
        dot = Dot(self.width, self.height)
        dot.speed = speed
        self.dots.append(dot)
