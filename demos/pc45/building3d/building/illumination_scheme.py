import random


class WindowIlluminationScheme:
    def __init__(self, lit_probability=0.4, random_seed=None):
        self.lit_probability = lit_probability
        self.random_source = random.Random(random_seed)

    def is_window_illuminated(self, floor_index, segment_index):
        return self.random_source.random() < self.lit_probability
