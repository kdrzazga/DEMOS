class BuildingColorPalette:
    def __init__(self,
                 facade_color=(0.82, 0.84, 0.87),
                 courtyard_wall_color=(0.34, 0.36, 0.40),
                 unlit_window_color=(0.09, 0.13, 0.22),
                 lit_window_color=(1.0, 0.86, 0.55),
                 shaft_color=(0.52, 0.55, 0.60),
                 roof_color=(0.44, 0.46, 0.50),
                 sign_panel_color=(0.55, 0.56, 0.58),
                 sign_background_color=(0.05, 0.05, 0.06),
                 sign_bar_color=(0.93, 0.94, 0.96),
                 ground_color=(0.07, 0.08, 0.10)):
        self.facade_color = facade_color
        self.courtyard_wall_color = courtyard_wall_color
        self.unlit_window_color = unlit_window_color
        self.lit_window_color = lit_window_color
        self.shaft_color = shaft_color
        self.roof_color = roof_color
        self.sign_panel_color = sign_panel_color
        self.sign_background_color = sign_background_color
        self.sign_bar_color = sign_bar_color
        self.ground_color = ground_color
