from lib.pixelove_ole.geometry import Gradient, SurfaceStyle, additive_blending, glow_disc, logo_point, voxel_block
from lib.pixelove_ole.glyphs import SPACE_INVADER
from lib.pixelove_ole.part import LogoPart


class SpaceInvader(LogoPart):
    """The green crab invader as a voxel sprite."""

    def __init__(self, x=None, y=None, z=-0.45, cell_size=0.155, depth=0.3, sprite=SPACE_INVADER):
        center_x, center_y = logo_point(812, 545)
        super().__init__("space_invader", center_x if x is None else x, center_y if y is None else y, z)
        self.cell_size = cell_size
        self.depth = depth
        self.sprite = sprite
        self.style = SurfaceStyle(Gradient((0.0, (0.75, 1.0, 0.35)), (1.0, (0.15, 0.85, 0.35))),
                                  side_near=(0.1, 0.55, 0.2), side_far=(0.02, 0.2, 0.08),
                                  edge=(0.85, 1.0, 0.7), edge_width=1.0)
        self.glow_color = (0.3, 1.0, 0.35)

    def build(self):
        voxel_block(self.sprite, self.cell_size, self.cell_size, self.depth, self.style)
        with additive_blending():
            glow_disc(0.0, 0.0, -self.depth / 2 - 0.01, self.cell_size * 8, self.glow_color, alpha=0.25)
