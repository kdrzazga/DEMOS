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
        self.hole_hold = 0.5
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
        self.first_wishes = 14.0
        self.second_wishes = 16.0



class Delay:
    """Waits in seconds before something starts in the WinterDemo."""

    def __init__(self):
        self.nebula = 2.0
        self.santa = 2.0

        self.desk_item = 0.35
        self.desk_start = 0.6
        self.hall_santa_fall = 2.0


class Globe:
    """The Earth globe seen in space and dived into."""

    def __init__(self):
        self.radius = 60.0
        self.tilt = 23.4
        self.longitude = 10.0
        self.latitude = 50.0
        self.spin_speed = 1.5


class SkyCloudCover:
    """The cloud shell around the Earth that the dive passes through."""

    def __init__(self):
        self.count = 130
        self.shell = (61.0, 78.0)
        self.core = 8.0
        self.spread = 24.0
        self.crowding = 1.6
        self.size = (5.0, 9.0)
        self.puffs = 9
        self.seed = 7
        self.haze_share = 0.5
        self.opacity = (0.25, 0.70)


class Glide:
    """The glide down from the clouds towards the city."""

    def __init__(self):
        self.speed = 40.0
        self.level = 2.5
        self.drop = 60.0
        self.altitude = 30.0
        self.site_ahead = 200.0
        self.site_aside = -8.0
        self.look_down = 5.0
        self.sky_fade = 3.0
        self.fog_end = 1600.0


class CityPlan:
    """Where the city stands and how it is generated."""

    def __init__(self):
        self.ahead = 580.0
        self.aside = 25.0
        self.matrix = 7
        self.sink = 0.0
        self.seed = 5
        self.flat_size = (176.0, 112.0)
        self.flat_falloff = 100.0


class InteriorCamera:
    """The camera inside the hall right after entering it."""

    def __init__(self):
        self.eye_setback = 4.0
        self.eye_height = 2.4
        self.look_height = 6.0
        self.sway = 3.0
        self.sway_speed = 0.5


class DeskLayout:
    """How the desks are arranged in the hall (hall-local frame)."""

    def __init__(self):
        self.rows = 3
        self.per_row = 2
        self.wall_margin = 1.0
        self.size = 2.5
        self.gap = 0.4
        self.row_spacing = 2.2
        self.nearest_row_z = 5.0


class FrontRowCamera:
    """The camera view over the first row of desks."""

    def __init__(self):
        self.eye_setback = 5.0
        self.eye_height = 4.2
        self.look_ahead = 8.0
        self.look_height = 1.9
        self.sway_left = 0.2


class HallSantaEntrance:
    """Santa dropping into the hall next to the big screen."""

    def __init__(self):
        self.size = 1.8
        self.side_gap = 1.4
        self.front_offset = 0.8
        self.foot_depth = 0.165
        self.drop_height = 14.0
        self.bounce_height = 0.7
