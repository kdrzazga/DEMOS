import math

from sine_roots3d import RootPatch, mix_colors


class PulsingPalette:
    def __init__(self):
        self.darkest_surface = (0, 0, 0)
        self.brightest_surface = (38, 38, 66)
        self.white = (245, 245, 240)
        self.cream = (240, 226, 190)
        self.period_seconds = 6.0
        self.elapsed_seconds = 0.0

    def update(self, delta_seconds):
        self.elapsed_seconds += delta_seconds

    def progress(self):
        return 0.5 - 0.5 * math.cos(2 * math.pi * self.elapsed_seconds / self.period_seconds)

    def surface_color(self):
        return mix_colors(self.darkest_surface, self.brightest_surface, self.progress())

    def shifting_root_color(self):
        return mix_colors(self.white, self.cream, self.progress())

    def patch_color(self, patch_index):
        if patch_index % 5 == 0:
            return self.white
        if patch_index % 5 == 1:
            return self.cream
        return self.shifting_root_color()


class OpeningSequence:
    def __init__(self, field):
        self.field = field
        self.small_size = 1.8
        self.big_size = 8.0
        self.pair_gap = 3.5
        self.big_almost_gone_progress = 0.8
        self.pair_halfway_progress = 0.5
        self.path_center_x = 0.0
        self.path_center_z = -4.0
        self.patches = []
        self.lead_patch = None
        self.stage = self.wait_for_single_to_leave
        self.field.hold_back_all()
        self.lead_patch = self.send(self.small_size, 0.0, 0)

    def send(self, size, sideways_offset, color_index):
        drift_per_depth = self.field.travel_right_speed / self.field.travel_toward_camera_speed
        start_z = self.field.far_edge_z - size / 2
        start_x = self.path_center_x + sideways_offset - drift_per_depth * (self.path_center_z - start_z)
        patch = RootPatch(start_x, start_z, size)
        self.field.dress(patch)
        patch.color_index = color_index
        self.patches.append(patch)
        return patch

    def has_left(self, patch):
        return patch.z - patch.size / 2 > self.field.near_edge_z

    def wait_for_single_to_leave(self):
        if self.lead_patch not in self.patches:
            self.lead_patch = self.send(self.big_size, 0.0, 1)
            self.stage = self.wait_for_big_to_almost_leave

    def wait_for_big_to_almost_leave(self):
        if self.field.path_progress(self.lead_patch) >= self.big_almost_gone_progress:
            self.lead_patch = self.send(self.small_size, -self.pair_gap / 2, 0)
            self.send(self.small_size, self.pair_gap / 2, 1)
            self.stage = self.wait_for_pair_to_reach_halfway

    def wait_for_pair_to_reach_halfway(self):
        if self.field.path_progress(self.lead_patch) >= self.pair_halfway_progress:
            self.field.release()
            self.stage = self.let_regular_waves_flow

    def let_regular_waves_flow(self):
        pass

    def update(self, delta_seconds):
        for patch in self.patches:
            self.field.move(patch, delta_seconds)
        self.patches = [patch for patch in self.patches if not self.has_left(patch)]
        self.stage()


def smooth_step(amount):
    amount = min(max(amount, 0.0), 1.0)
    return amount * amount * (3.0 - 2.0 * amount)


class PulseShow:
    def __init__(self, roots):
        self.roots = roots
        self.lean_starts_at_seconds = 20.0
        self.lean_settles_at_seconds = 25.0
        self.settle_duration_seconds = 1.5
        self.lean_swing_degrees = 20.0
        self.lean_period_seconds = 3.0
        self.default_lean_degrees = 0.0
        self.elapsed_seconds = 0.0
        self.palette = None
        self.opening = None

    def start(self):
        self.elapsed_seconds = 0.0
        self.palette = PulsingPalette()
        self.opening = OpeningSequence(self.roots.field)
        self.roots.start_show(self)

    def is_leaning(self):
        settled_at = self.lean_settles_at_seconds + self.settle_duration_seconds
        return self.lean_starts_at_seconds <= self.elapsed_seconds <= settled_at

    def lean_degrees(self):
        seconds_leaning = self.elapsed_seconds - self.lean_starts_at_seconds
        swing = self.lean_swing_degrees * math.sin(2 * math.pi * seconds_leaning / self.lean_period_seconds)
        settling = smooth_step((self.elapsed_seconds - self.lean_settles_at_seconds) / self.settle_duration_seconds)
        return self.default_lean_degrees + swing * (1.0 - settling)

    def update(self, delta_seconds):
        self.elapsed_seconds += delta_seconds
        if self.is_leaning():
            self.roots.surface_tilt_degrees = self.lean_degrees()
