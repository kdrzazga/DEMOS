from .window_panel import WindowPanel


class FacadeSegment:
    def __init__(self, start_angle, end_angle, bottom_height, top_height,
                 outer_footprint, inner_footprint, window_footprint,
                 window_margin_ratio, window_sill_ratio, window_rows_per_floor,
                 wall_color, window_colors):
        self.wall_color = wall_color
        self.outer_wall_corners = self.build_outer_facing_wall(
            outer_footprint, start_angle, end_angle, bottom_height, top_height)
        self.inner_wall_corners = self.build_courtyard_facing_wall(
            inner_footprint, start_angle, end_angle, bottom_height, top_height)
        self.window_panels = self.build_stacked_window_panels(
            window_footprint, start_angle, end_angle, bottom_height, top_height,
            window_margin_ratio, window_sill_ratio, window_rows_per_floor, window_colors)

    def build_outer_facing_wall(self, footprint, start_angle, end_angle, bottom_height, top_height):
        return (
            footprint.perimeter_point(start_angle, bottom_height),
            footprint.perimeter_point(end_angle, bottom_height),
            footprint.perimeter_point(end_angle, top_height),
            footprint.perimeter_point(start_angle, top_height),
        )

    def build_courtyard_facing_wall(self, footprint, start_angle, end_angle, bottom_height, top_height):
        return (
            footprint.perimeter_point(end_angle, bottom_height),
            footprint.perimeter_point(start_angle, bottom_height),
            footprint.perimeter_point(start_angle, top_height),
            footprint.perimeter_point(end_angle, top_height),
        )

    def build_stacked_window_panels(self, footprint, start_angle, end_angle, bottom_height,
                                    top_height, window_margin_ratio, window_sill_ratio,
                                    window_rows_per_floor, window_colors):
        angular_span = end_angle - start_angle
        window_start_angle = start_angle + angular_span * window_margin_ratio
        window_end_angle = end_angle - angular_span * window_margin_ratio
        row_height = (top_height - bottom_height) / window_rows_per_floor
        stacked_panels = []
        for row_index in range(window_rows_per_floor):
            row_bottom_height = bottom_height + row_height * row_index
            window_bottom_height = row_bottom_height + row_height * window_sill_ratio
            window_top_height = row_bottom_height + row_height * (1.0 - window_sill_ratio)
            corner_points = (
                footprint.perimeter_point(window_start_angle, window_bottom_height),
                footprint.perimeter_point(window_end_angle, window_bottom_height),
                footprint.perimeter_point(window_end_angle, window_top_height),
                footprint.perimeter_point(window_start_angle, window_top_height),
            )
            stacked_panels.append(WindowPanel(corner_points, window_colors[row_index]))
        return tuple(stacked_panels)

    def render_using(self, renderer, palette):
        renderer.render_shaded_quad(self.outer_wall_corners, self.wall_color)
        renderer.render_shaded_quad(self.inner_wall_corners, palette.courtyard_wall_color)
        for window_panel in self.window_panels:
            window_panel.render_using(renderer)
