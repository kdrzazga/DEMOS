from .color_gradient import ColorGradient
from .patch_color_field import PatchColorField


class FacadeColorScheme:
    def __init__(self, random_seed=11, patch_feature_scale=4.0):
        self.facade_gradient = ColorGradient((
            (0.0, (1.0, 1.0, 1.0)),
            (1.0, (0.78, 0.78, 0.80)),
        ))
        self.unlit_window_gradient = ColorGradient((
            (0.0, (1.0, 1.0, 1.0)),
            (0.5, (0.60, 0.78, 1.0)),
            (1.0, (0.0, 0.0, 1.0)),
        ))
        self.lit_window_gradient = ColorGradient((
            (0.0, (1.0, 1.0, 1.0)),
            (0.35, (1.0, 1.0, 0.75)),
            (0.70, (1.0, 0.88, 0.20)),
            (1.0, (1.0, 0.50, 0.05)),
        ))
        self.facade_patch_field = PatchColorField(patch_feature_scale, random_seed + 1)
        self.window_patch_field = PatchColorField(patch_feature_scale, random_seed + 2)

    def facade_color_at(self, floor_index, segment_index):
        patch_value = self.facade_patch_field.sample(segment_index, floor_index)
        return self.facade_gradient.sample(patch_value)

    def window_color_at(self, floor_index, segment_index, is_illuminated):
        patch_value = self.window_patch_field.sample(segment_index, floor_index)
        chosen_gradient = self.lit_window_gradient if is_illuminated else self.unlit_window_gradient
        return chosen_gradient.sample(patch_value)
