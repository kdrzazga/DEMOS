import math
import random


class PatchColorField:
    def __init__(self, feature_scale=4.0, seed=0):
        self.feature_scale = feature_scale
        self.seed = seed

    def lattice_value(self, lattice_x, lattice_y):
        deterministic_source = random.Random(
            (lattice_x * 73856093) ^ (lattice_y * 19349663) ^ (self.seed * 83492791))
        return deterministic_source.random()

    def sample(self, column, floor):
        scaled_column = column / self.feature_scale
        scaled_floor = floor / self.feature_scale
        cell_column = math.floor(scaled_column)
        cell_floor = math.floor(scaled_floor)
        column_fraction = self.smoothstep(scaled_column - cell_column)
        floor_fraction = self.smoothstep(scaled_floor - cell_floor)
        bottom_left = self.lattice_value(cell_column, cell_floor)
        bottom_right = self.lattice_value(cell_column + 1, cell_floor)
        top_left = self.lattice_value(cell_column, cell_floor + 1)
        top_right = self.lattice_value(cell_column + 1, cell_floor + 1)
        bottom_blend = self.linear_blend(bottom_left, bottom_right, column_fraction)
        top_blend = self.linear_blend(top_left, top_right, column_fraction)
        return self.linear_blend(bottom_blend, top_blend, floor_fraction)

    def smoothstep(self, fraction):
        return fraction * fraction * (3.0 - 2.0 * fraction)

    def linear_blend(self, first_value, second_value, fraction):
        return first_value + (second_value - first_value) * fraction
