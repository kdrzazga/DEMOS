class Duration:
    """Lengths in seconds of the WinterDemo scenes and of the moves inside them."""

    def __init__(self):
        self.sway = 5.0
        self.travel = 2.5
        self.settle = 4.0
        self.enter = 3.0
        self.igloo_show = 6.0
        self.ascend = 4.6
        self.hole_tilt = 0.4
        self.hole_hoold = 0.5
        self.hole_gaze = self.hole_tilt + self.hole_hold
        self.space = 10.0

        self.ride = 5.0
        self.planets = 17.0
        self.turn = 1.4
        self.approach = 8.0
        self.glide = 15.0
        self.landing = 5.0
        self.rooftop = 4.2
        self.jump = 1.6

        self.desk_empty_hall = 2.0
        self.desk_settle = 1.0
        self.hall_darken = 2.0
        self.front_row_approach = 4.0
        self.front_row_hold = 1.0
        self.screen_fade = 1.5
        self.screen_approach = 4.0
        self.hall_santa_fall = 1.3
        self.hall_santa_bounce = 0.45
        self.hall_final_hold = 3.0



class Delay:
    """Waits in seconds before something starts in the WinterDemo."""

    def __init__(self):
        self.nebula = 2.0
        self.santa = 2.0

        self.desk_item = 0.35
        self.desk_start = 0.6
        self.hall_santa_fall = 2.0
