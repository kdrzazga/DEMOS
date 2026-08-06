from .building.color_gradient import ColorGradient
from .building.patch_color_field import PatchColorField
from .linear_algebra import Vector3


class GroundPlane:
    def __init__(self, half_extent=140.0, height=0.0, tile_count=40,
                 brown_color=(0.40, 0.26, 0.13), dark_green_color=(0.11, 0.22, 0.09),
                 patch_feature_scale=4.0, random_seed=23):
        self.terrain_gradient = ColorGradient((
            (0.0, brown_color),
            (0.5, brown_color),
            (1.0, dark_green_color),
        ))
        self.patch_field = PatchColorField(patch_feature_scale, random_seed)
        self.colored_tiles = self.build_colored_tiles(half_extent, height, tile_count)

    def build_colored_tiles(self, half_extent, height, tile_count):
        constructed_tiles = []
        tile_size = (2.0 * half_extent) / tile_count
        for tile_z in range(tile_count):
            for tile_x in range(tile_count):
                near_x = -half_extent + tile_size * tile_x
                far_x = near_x + tile_size
                near_z = -half_extent + tile_size * tile_z
                far_z = near_z + tile_size
                corner_points = (
                    Vector3(near_x, height, near_z),
                    Vector3(far_x, height, near_z),
                    Vector3(far_x, height, far_z),
                    Vector3(near_x, height, far_z),
                )
                patch_value = self.patch_field.sample(tile_x, tile_z)
                tile_color = self.terrain_gradient.sample(patch_value)
                constructed_tiles.append((corner_points, tile_color))
        return tuple(constructed_tiles)

    def render_using(self, renderer, palette):
        for corner_points, tile_color in self.colored_tiles:
            renderer.render_shaded_quad(corner_points, tile_color)
