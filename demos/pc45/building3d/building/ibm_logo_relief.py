class IbmLogoRelief:
    def __init__(self, base_footprint, raised_footprint, start_angle, end_angle,
                 bottom_height, top_height, horizontal_margin_fraction=0.08,
                 vertical_fill_fraction=0.92, row_fill_ratio=0.66):
        self.logo_rows = (
            "1111110011111100011000011",
            "1111110011111110011100111",
            "0011000011000110011111111",
            "0011000011111100011011011",
            "0011000011111110011011011",
            "0011000011000110011000011",
            "1111110011111110011000011",
            "1111110011111100011000011",
        )
        self.bar_faces = self.build_bar_faces(
            base_footprint, raised_footprint, start_angle, end_angle, bottom_height,
            top_height, horizontal_margin_fraction, vertical_fill_fraction, row_fill_ratio)

    def build_bar_faces(self, base_footprint, raised_footprint, start_angle, end_angle,
                        bottom_height, top_height, horizontal_margin_fraction,
                        vertical_fill_fraction, row_fill_ratio):
        row_count = len(self.logo_rows)
        column_count = len(self.logo_rows[0])
        angular_span = end_angle - start_angle
        left_angle = end_angle - angular_span * horizontal_margin_fraction
        right_angle = start_angle + angular_span * horizontal_margin_fraction
        column_angular_step = (left_angle - right_angle) / column_count

        middle_height = 0.5 * (bottom_height + top_height)
        panel_world_width = self.estimate_world_width(base_footprint, left_angle, right_angle, middle_height)
        logo_world_height = min(panel_world_width * row_count / column_count,
                                (top_height - bottom_height) * vertical_fill_fraction)
        logo_top_height = middle_height + 0.5 * logo_world_height
        row_height = logo_world_height / row_count

        constructed_faces = []
        for row_index in range(row_count):
            band_top_height = logo_top_height - row_height * row_index
            band_bottom_height = band_top_height - row_height
            vertical_gap = row_height * (1.0 - row_fill_ratio) * 0.5
            bar_bottom_height = band_bottom_height + vertical_gap
            bar_top_height = band_top_height - vertical_gap
            for run_start, run_end in self.find_horizontal_runs(self.logo_rows[row_index]):
                bar_left_angle = left_angle - column_angular_step * run_start
                bar_right_angle = left_angle - column_angular_step * (run_end + 1)
                constructed_faces.extend(self.build_raised_bar(
                    base_footprint, raised_footprint, bar_left_angle, bar_right_angle,
                    bar_bottom_height, bar_top_height))
        return tuple(constructed_faces)

    def estimate_world_width(self, footprint, angle_a, angle_b, height):
        point_a = footprint.perimeter_point(angle_a, height)
        point_b = footprint.perimeter_point(angle_b, height)
        return point_a.subtracted_by(point_b).magnitude()

    def find_horizontal_runs(self, row_pattern):
        runs = []
        run_start = None
        for column_index, cell in enumerate(row_pattern):
            if cell == "1" and run_start is None:
                run_start = column_index
            elif cell != "1" and run_start is not None:
                runs.append((run_start, column_index - 1))
                run_start = None
        if run_start is not None:
            runs.append((run_start, len(row_pattern) - 1))
        return tuple(runs)

    def build_raised_bar(self, base_footprint, raised_footprint, left_angle, right_angle,
                         bottom_height, top_height):
        base_bottom_left = base_footprint.perimeter_point(left_angle, bottom_height)
        base_bottom_right = base_footprint.perimeter_point(right_angle, bottom_height)
        base_top_left = base_footprint.perimeter_point(left_angle, top_height)
        base_top_right = base_footprint.perimeter_point(right_angle, top_height)
        raised_bottom_left = raised_footprint.perimeter_point(left_angle, bottom_height)
        raised_bottom_right = raised_footprint.perimeter_point(right_angle, bottom_height)
        raised_top_left = raised_footprint.perimeter_point(left_angle, top_height)
        raised_top_right = raised_footprint.perimeter_point(right_angle, top_height)

        front_face = (raised_bottom_left, raised_bottom_right, raised_top_right, raised_top_left)
        bottom_face = (base_bottom_left, base_bottom_right, raised_bottom_right, raised_bottom_left)
        top_face = (raised_top_left, raised_top_right, base_top_right, base_top_left)
        left_face = (base_bottom_left, raised_bottom_left, raised_top_left, base_top_left)
        right_face = (raised_bottom_right, base_bottom_right, base_top_right, raised_top_right)
        return (front_face, bottom_face, top_face, left_face, right_face)

    def render_using(self, renderer, bar_color):
        for bar_face in self.bar_faces:
            renderer.render_shaded_quad(bar_face, bar_color)
