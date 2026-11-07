import math
import random as random_module

import pygame


class SineRoot:
    def __init__(self, origin, heading, thickness, birth_seconds, random):
        self.origin_x, self.origin_y = origin
        self.heading = heading
        self.thickness = thickness
        self.birth_seconds = birth_seconds
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

    def points_grown_by(self, distance):
        distance = min(distance, self.travelled)
        whole_steps = int(distance)
        grown_points = self.points[:whole_steps + 1]
        if distance > whole_steps:
            grown_points.append(self.position_at(distance))
        return grown_points


class SineRootGrowth:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        self.random = random_module.Random(seed)
        self.time_scale = 3.0
        self.fast_forward_after_seconds = 2.0
        self.fast_forward_factor = 10.0
        self.turnaround_seconds = 60.0
        self.bounce_lowest_progress = 0.3
        self.initial_root_count = 5
        self.growth_speed = 6.0
        self.speed_factor_minimum = 1.0
        self.speed_factor_maximum = 2.0
        self.initial_thickness = 4.0
        self.thickness_kept_after_split = 0.8
        self.minimum_thickness = 1.0
        self.split_angle_base_degrees = 45.0
        self.split_angle_random_degrees = 20.0
        self.maximum_root_count = 4000
        self.branch_visible_seconds = 40.0
        self.edge_margin = 20
        self.background_color = (226, 229, 235)
        self.root_color = (24, 20, 20)
        self.canvas = pygame.Surface((width, height))
        self.restart()

    def restart(self):
        self.canvas.fill(self.background_color)
        self.elapsed_seconds = 0.0
        self.real_elapsed_seconds = 0.0
        self.is_still_growing = True
        self.playback_direction = 1.0
        self.sections = []
        center = (self.width / 2, self.height / 2)
        first_heading = self.random.random() * math.pi + math.pi
        spacing = 2 * math.pi / self.initial_root_count
        self.roots = [self.plant(center, first_heading + index * spacing, self.initial_thickness)
                      for index in range(self.initial_root_count)]

    def plant(self, origin, heading, thickness):
        root = SineRoot(origin, heading, thickness, self.elapsed_seconds, self.random)
        speed_factor = self.random.uniform(self.speed_factor_minimum, self.speed_factor_maximum)
        root.growth_speed = self.growth_speed * speed_factor
        self.sections.append(root)
        return root

    def split(self, root):
        r = 0.5 + 0.5*self.random.random()
        spread = math.radians(self.split_angle_base_degrees
                              + self.split_angle_random_degrees * r)
        thickness = max(self.minimum_thickness, root.thickness * self.thickness_kept_after_split)
        return [self.plant(root.tip, root.heading - spread / 2, thickness),
                self.plant(root.tip, root.heading + spread / 2, thickness)]

    def paint_branch(self, root, points):
        if len(points) < 2:
            return
        line_width = max(1, round(root.thickness))
        pygame.draw.lines(self.canvas, self.root_color, False, points, line_width)
        if line_width > 2:
            for point in points[::2]:
                pygame.draw.circle(self.canvas, self.root_color, point, root.thickness / 2)

    def repaint(self):
        self.canvas.fill(self.background_color)
        for section in self.sections:
            section_age = self.elapsed_seconds - section.birth_seconds
            if 0.0 < section_age < self.branch_visible_seconds:
                self.paint_branch(section, section.points_grown_by(section_age * section.growth_speed))

    def grow(self, root, distance):
        target_distance = root.travelled + distance
        while root.travelled < target_distance:
            root.travelled = min(root.travelled + 1.0, target_distance)
            root.points.append(root.position_at(root.travelled))

    def is_on_canvas(self, point):
        x, y = point
        return (-self.edge_margin <= x <= self.width + self.edge_margin
                and -self.edge_margin <= y <= self.height + self.edge_margin)

    def simulate(self, delta_seconds):
        surviving_roots = []
        for root in self.roots:
            root.age_seconds += delta_seconds
            self.grow(root, root.growth_speed * delta_seconds)
            if not self.is_on_canvas(root.tip):
                continue
            if root.is_ready_to_split() and len(self.roots) + len(surviving_roots) < self.maximum_root_count:
                surviving_roots.extend(self.split(root))
            else:
                surviving_roots.append(root)

            root.split_after_seconds = root.split_after_seconds + 0.1
        self.roots = surviving_roots

    def keep_growing(self, delta_seconds):
        growth_step = min(delta_seconds, self.turnaround_seconds - self.elapsed_seconds)
        self.elapsed_seconds += growth_step
        self.simulate(growth_step)
        if self.elapsed_seconds >= self.turnaround_seconds:
            self.is_still_growing = False
            self.playback_direction = -1.0

    def bounce(self, delta_seconds):
        self.elapsed_seconds += delta_seconds * self.playback_direction
        lowest_seconds = self.turnaround_seconds * self.bounce_lowest_progress
        if self.elapsed_seconds <= lowest_seconds:
            self.elapsed_seconds = lowest_seconds
            self.playback_direction = 1.0
        elif self.elapsed_seconds >= self.turnaround_seconds:
            self.elapsed_seconds = self.turnaround_seconds
            self.playback_direction = -1.0

    def update(self, delta_seconds):
        self.real_elapsed_seconds += delta_seconds
        delta_seconds *= self.time_scale
        if self.real_elapsed_seconds > self.fast_forward_after_seconds:
            delta_seconds *= self.fast_forward_factor
        if self.is_still_growing:
            self.keep_growing(delta_seconds)
        else:
            self.bounce(delta_seconds)
        self.repaint()

    def draw(self, target):
        if target.get_size() == self.canvas.get_size():
            target.blit(self.canvas, (0, 0))
        else:
            pygame.transform.smoothscale(self.canvas, target.get_size(), target)
