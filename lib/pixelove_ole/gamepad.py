from lib.pixelove_ole.geometry import (Gradient, SurfaceStyle, additive_blending, circle_points, ellipse_points,
                                       extrude_polygon, glow_segment, grow_points, logo_point, rounded_rect_points,
                                       solid)
from lib.pixelove_ole.part import LogoPart


class Gamepad(LogoPart):
    """Dark controller with a neon-blue rim, purple d-pad, four coloured
    face buttons and two thumbsticks. Built from convex pieces, so the body
    is a rounded centre plate plus two tilted grip ellipses."""

    def __init__(self, x=None, y=None, z=-0.45, tilt=-22.0, depth=0.3):
        center_x, center_y = logo_point(172, 590)
        super().__init__("gamepad", center_x if x is None else x, center_y if y is None else y, z)
        self.roll = tilt
        self.home_roll = tilt
        self.depth = depth
        self.body_style = SurfaceStyle(Gradient((0.0, (0.14, 0.15, 0.38)), (1.0, (0.04, 0.04, 0.14))),
                                       side_near=(0.1, 0.1, 0.3), side_far=(0.03, 0.03, 0.1))
        self.rim_style = SurfaceStyle(Gradient((0.0, (0.55, 0.85, 1.0)), (1.0, (0.55, 0.3, 1.0))),
                                      side_near=(0.3, 0.55, 1.0), side_far=(0.15, 0.1, 0.5))
        self.rim_glow = (0.3, 0.6, 1.0)
        self.dpad_color = (0.7, 0.5, 1.0)
        self.button_colors = {(0.0, 1.0): (1.0, 0.45, 0.65), (-1.0, 0.0): (1.0, 0.25, 0.35),
                              (1.0, 0.0): (1.0, 0.85, 0.2), (0.0, -1.0): (0.3, 0.65, 1.0)}
        self.stick_color = (0.08, 0.08, 0.2)
        self.stick_rim = (0.4, 0.45, 0.9)

    def go_home(self):
        super().go_home()
        self.roll = self.home_roll

    def body_pieces(self):
        return (rounded_rect_points(0.0, 0.12, 1.35, 0.72, 0.28),
                ellipse_points(-0.5, -0.22, 0.27, 0.48, -28.0),
                ellipse_points(0.5, -0.22, 0.27, 0.48, 28.0))

    def button(self, center, radius, color, height):
        style = SurfaceStyle(Gradient((0.0, (1.0, 1.0, 1.0)), (0.35, color), (1.0, color)),
                             side_near=color, side_far=color)
        extrude_polygon(circle_points(*center, radius, 20), height, style, z=self.depth / 2 + height / 2)

    def build(self):
        for piece in self.body_pieces():
            extrude_polygon(grow_points(piece, 0.05), self.depth * 0.7, self.rim_style, z=-self.depth * 0.2)
            extrude_polygon(piece, self.depth, self.body_style)

        front = self.depth / 2
        dpad_style = SurfaceStyle(solid(self.dpad_color), self.dpad_color, edge=(1.0, 0.9, 1.0), edge_width=1.0)
        dpad_x, dpad_y, arm, thickness = -0.4, 0.14, 0.14, 0.055
        extrude_polygon(rounded_rect_points(dpad_x, dpad_y, arm * 2, thickness * 2, 0.02, 2), 0.08,
                        dpad_style, z=front + 0.04)
        extrude_polygon(rounded_rect_points(dpad_x, dpad_y, thickness * 2, arm * 2, 0.02, 2), 0.08,
                        dpad_style, z=front + 0.04)

        buttons_x, buttons_y, spread = 0.4, 0.14, 0.12
        for (offset_x, offset_y), color in self.button_colors.items():
            self.button((buttons_x + offset_x * spread, buttons_y + offset_y * spread), 0.055, color, 0.07)

        stick_style = SurfaceStyle(Gradient((0.0, self.stick_rim), (0.25, self.stick_color), (1.0, self.stick_color)),
                                   side_near=self.stick_rim, side_far=self.stick_color, edge=self.stick_rim)
        for stick_x in (-0.17, 0.17):
            extrude_polygon(circle_points(stick_x, -0.12, 0.1, 24), 0.12, stick_style, z=front + 0.06)

        outline = grow_points(self.body_pieces()[0], 0.06)
        with additive_blending():
            for start, end in zip(outline, outline[1:] + outline[:1]):
                glow_segment(start, end, -self.depth / 2, 0.25, self.rim_glow, alpha=0.3)
