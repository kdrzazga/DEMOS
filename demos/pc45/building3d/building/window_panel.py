class WindowPanel:
    def __init__(self, corner_points, window_color):
        self.corner_points = corner_points
        self.window_color = window_color

    def render_using(self, renderer):
        renderer.render_emissive_quad(self.corner_points, self.window_color)
