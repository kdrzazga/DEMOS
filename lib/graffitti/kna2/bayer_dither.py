import math

import numpy as np


class BayerDither:

	def __init__(self):
		self.cell = 3
		self.irregularity = 0.0
		self.noise_seed = 5
		self.matrix = np.array([[0, 8, 2, 10],
		                        [12, 4, 14, 6],
		                        [3, 11, 1, 9],
		                        [15, 7, 13, 5]], dtype=np.float32)

	def grid_size(self, size):
		return math.ceil(size[0] / self.cell), math.ceil(size[1] / self.cell)

	def cell_thresholds(self, grid_size):
		columns, rows = np.mgrid[0:grid_size[0], 0:grid_size[1]]
		matrix_size = self.matrix.shape[0]
		ordered = (self.matrix[columns % matrix_size, rows % matrix_size] + 0.5) / self.matrix.size
		noise = np.random.default_rng(self.noise_seed).random(grid_size, dtype=np.float32)
		return ordered * (1.0 - self.irregularity) + noise * self.irregularity

	def enlarged(self, cell_values, size):
		return np.repeat(np.repeat(cell_values, self.cell, axis=0), self.cell, axis=1)[:size[0], :size[1]]

	def thresholds(self, size):
		return self.enlarged(self.cell_thresholds(self.grid_size(size)), size)

	def dotted_area(self, intensity):
		return intensity > self.thresholds(intensity.shape)
