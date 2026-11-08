class NeonPalette:

    def __init__(self):
        self.tube_colors = (
            (60, 240, 230),
            (255, 220, 60),
            (255, 70, 90),
            (255, 110, 190),
            (110, 255, 140),
            (255, 150, 40),
            (210, 255, 240),
            (90, 160, 255),
        )
        self.backgrounds = (
            (12, 18, 20),
            (30, 10, 14),
            (8, 26, 22),
            (40, 36, 8),
            (230, 230, 220),
            (200, 40, 50),
            (20, 120, 120),
        )
        self.window_lights = ((255, 210, 120), (150, 230, 210), (240, 240, 220), (255, 160, 90))
        self.skin = (0.86, 0.66, 0.55)
        self.hair = (0.07, 0.05, 0.05)
        self.shorts = (0.06, 0.06, 0.07)
        self.metal = (0.08, 0.09, 0.09)
        self.fog = (0.1, 0.17, 0.14, 1.0)
        self.asphalt = (0.05, 0.07, 0.065, 0.62)
        self.car_bodies = ((0.95, 0.78, 0.15), (0.95, 0.78, 0.15), (0.75, 0.1, 0.12),
                           (0.12, 0.14, 0.16), (0.8, 0.82, 0.8), (0.1, 0.35, 0.4))
        self.headlight = (1.0, 0.95, 0.8)
        self.taillight = (1.0, 0.15, 0.1)
        self.street_lamp = (1.0, 0.75, 0.4)

    def tube(self, randomness):
        return randomness.choice(self.tube_colors)

    def background(self, randomness):
        return randomness.choice(self.backgrounds)

    def contrasting_tube(self, randomness, background):
        brightness = sum(background) / 3.0
        if brightness > 150:
            return randomness.choice(((20, 20, 20), (200, 20, 40), (10, 90, 90)))
        return self.tube(randomness)
