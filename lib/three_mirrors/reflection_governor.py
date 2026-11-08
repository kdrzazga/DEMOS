class ReflectionGovernor:

    def __init__(self, renderer, frames_per_second):
        self.renderer = renderer
        self.target_frame_seconds = 1.0 / frames_per_second
        self.slow_ratio = 1.12
        self.fast_ratio = 1.03
        self.smoothing = 0.1
        self.fewest = 2
        self.most = 16
        self.cut_after = 0.5
        self.grow_after = 2.0
        self.smoothed_frame_seconds = self.target_frame_seconds
        self.since_change = 0.0
        self.renderer.reflection_budget = 8

    def observe(self, frame_seconds):
        self.smoothed_frame_seconds += (frame_seconds - self.smoothed_frame_seconds) * self.smoothing
        self.since_change += frame_seconds
        budget = self.renderer.reflection_budget
        if self.is_slow() and self.since_change >= self.cut_after and budget > self.fewest:
            self._settle(budget - 1)
        elif self.is_fast() and self.since_change >= self.grow_after and budget < self.most:
            self._settle(budget + 1)

    def is_slow(self):
        return self.smoothed_frame_seconds > self.target_frame_seconds * self.slow_ratio

    def is_fast(self):
        return self.smoothed_frame_seconds < self.target_frame_seconds * self.fast_ratio

    def _settle(self, budget):
        self.renderer.reflection_budget = budget
        self.since_change = 0.0

    @property
    def frames_per_second(self):
        return 1.0 / max(self.smoothed_frame_seconds, 1e-6)
