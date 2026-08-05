class ColorGradient:
    def __init__(self, color_stops):
        self.color_stops = color_stops

    def sample(self, value):
        clamped_value = max(0.0, min(1.0, value))
        previous_position, previous_color = self.color_stops[0]
        for position, color in self.color_stops:
            if clamped_value <= position:
                span = position - previous_position
                local_fraction = 0.0 if span == 0.0 else (clamped_value - previous_position) / span
                return self.blend_colors(previous_color, color, local_fraction)
            previous_position, previous_color = position, color
        return self.color_stops[-1][1]

    def blend_colors(self, first_color, second_color, fraction):
        return (
            first_color[0] + (second_color[0] - first_color[0]) * fraction,
            first_color[1] + (second_color[1] - first_color[1]) * fraction,
            first_color[2] + (second_color[2] - first_color[2]) * fraction,
        )
