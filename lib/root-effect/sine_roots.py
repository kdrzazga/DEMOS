import math
import random as random_module

import pygame


class SineRoot:
    def __init__(self, origin, heading, thickness, random):
        self.origin_x, self.origin_y = origin
        self.heading = heading
        self.thickness = thickness
        self.amplitude = 6.0 + 8.0 * random.random()
        self.wavelength = 100.0 + 10.0 * random.random()
        self.swing_sign = random.choice((-1.0, 1.0))
        self.split_time_base = 1/25
        self.split_after_seconds = self.split_time_base + 1.0 * random.random()
        self.age_seconds = 0.0
        self.travelled = 0.0
        self.points = [self.position_at(0.0)]

    @property
    def tip(self):
        return self.points[-1]

    def position_at(self, distance):
        sway = self.swing_sign * self.amplitude * math.sin(2 * math.pi * distance / self.wavelength)
        forward_x, forward_y = math.cos(self.heading), math.sin(self.heading)
        return (self.origin_x + forward_x * distance - forward_y * sway,
                self.origin_y + forward_y * distance + forward_x * sway)

    def is_ready_to_split(self):
        return self.age_seconds >= self.split_after_seconds


class SineRootGrowth:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        self.random = random_module.Random(seed)
        self.initial_root_count = 5
        self.growth_speed = 6.0
        self.initial_thickness = 4.0
        self.thickness_kept_after_split = 0.8
        self.minimum_thickness = 1.0
        self.split_angle_base_degrees = 45.0
        self.split_angle_random_degrees = 20.0
        self.maximum_root_count = 4000
        self.branch_visible_seconds = 22.0
        self.edge_margin = 20
        self.background_color = (226, 229, 235)
        self.root_color = (24, 20, 20)
        self.canvas = pygame.Surface((width, height))
        self.restart()

    def restart(self):
        self.canvas.fill(self.background_color)
        self.elapsed_seconds = 0.0
        center = (self.width / 2, self.height / 2)
        first_heading = self.random.random() * math.pi + math.pi
        spacing = 2 * math.pi / self.initial_root_count
        self.roots = [SineRoot(center, first_heading + index * spacing, self.initial_thickness, self.random)
                      for index in range(self.initial_root_count)]
        self.finished_roots = []

    def split(self, root):
        r = 0.5 + 0.5*self.random.random()
        spread = math.radians(self.split_angle_base_degrees
                              + self.split_angle_random_degrees * r)
        thickness = max(self.minimum_thickness, root.thickness * self.thickness_kept_after_split)
        return [SineRoot(root.tip, root.heading - spread / 2, thickness, self.random),
                SineRoot(root.tip, root.heading + spread / 2, thickness, self.random)]

    def paint_branch(self, root):
        if len(root.points) < 2:
            return
        line_width = max(1, round(root.thickness))
        pygame.draw.lines(self.canvas, self.root_color, False, root.points, line_width)
        if line_width > 2:
            for point in root.points[::2]:
                pygame.draw.circle(self.canvas, self.root_color, point, root.thickness / 2)

    def repaint(self):
        self.canvas.fill(self.background_color)
        for root in self.finished_roots:
            self.paint_branch(root)
        for root in self.roots:
            if self.is_visible(root):
                self.paint_branch(root)

    def grow(self, root, distance):
        target_distance = root.travelled + distance
        while root.travelled < target_distance:
            root.travelled = min(root.travelled + 1.0, target_distance)
            root.points.append(root.position_at(root.travelled))

    def is_visible(self, root):
        return root.age_seconds < self.branch_visible_seconds

    def is_on_canvas(self, point):
        x, y = point
        return (-self.edge_margin <= x <= self.width + self.edge_margin
                and -self.edge_margin <= y <= self.height + self.edge_margin)

    def update(self, delta_seconds):
        self.elapsed_seconds += delta_seconds
        for root in self.finished_roots:
            root.age_seconds += delta_seconds
        self.finished_roots = [root for root in self.finished_roots if self.is_visible(root)]
        surviving_roots = []
        for root in self.roots:
            root.age_seconds += delta_seconds
            self.grow(root, self.growth_speed * delta_seconds)
            if not self.is_on_canvas(root.tip):
                self.finished_roots.append(root)
                continue
            if root.is_ready_to_split() and len(self.roots) + len(surviving_roots) < self.maximum_root_count:
                self.finished_roots.append(root)
                surviving_roots.extend(self.split(root))
            else:
                surviving_roots.append(root)

            root.split_after_seconds = root.split_after_seconds + 0.1
        self.roots = surviving_roots
        self.repaint()


    def draw(self, target):
        if target.get_size() == self.canvas.get_size():
            target.blit(self.canvas, (0, 0))
        else:
            pygame.transform.smoothscale(self.canvas, target.get_size(), target)
