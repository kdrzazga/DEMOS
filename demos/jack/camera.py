import math


class Framing:
    def __init__(self, name, latitude, longitude, distance, focus, sign_scale, drift=0.0, sway=0.0, sway_period=9.0):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
        self.focus = focus
        self.sign_scale = sign_scale
        self.drift = drift
        self.sway = sway
        self.sway_period = sway_period


class GlobeCamera:
    def __init__(self, framing, view_offset=25.0, base_seconds=1.5, seconds_per_quarter_turn=1.0,
                 longest_glide=3.5, lift_per_degree=0.12, highest_lift=12.0, sway_ramp_seconds=1.5):
        self.view_offset = view_offset
        self.sway_ramp_seconds = sway_ramp_seconds
        self.sway_weight = 0.0
        self.sway_time = 0.0
        self.base_seconds = base_seconds
        self.seconds_per_quarter_turn = seconds_per_quarter_turn
        self.longest_glide = longest_glide
        self.lift_per_degree = lift_per_degree
        self.highest_lift = highest_lift
        self.latitude = framing.latitude
        self.longitude = framing.longitude
        self.distance = framing.distance
        self.focus = framing.focus
        self.target = framing
        self.origin = None
        self.turn = 0.0
        self.lift = 0.0
        self.duration = 0.0
        self.elapsed = 0.0

    @property
    def arrived(self):
        return self.elapsed >= self.duration

    def remaining_seconds(self):
        return max(0.0, self.duration - self.elapsed)

    def _separation(self, framing):
        latitude, target_latitude = math.radians(self.latitude), math.radians(framing.latitude)
        spread = math.radians(framing.longitude - self.longitude)
        cosine = (math.sin(latitude) * math.sin(target_latitude)
                  + math.cos(latitude) * math.cos(target_latitude) * math.cos(spread))
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))

    def _sway_offset(self):
        swing = math.sin(2.0 * math.pi * self.sway_time / self.target.sway_period)
        return self.target.sway * self.sway_weight * swing

    def view_longitude(self):
        return self.longitude + self._sway_offset()

    def _settle_sway(self):
        self.longitude = self.view_longitude()
        self.sway_weight = 0.0
        self.sway_time = 0.0

    def glide_to(self, framing):
        separation = self._separation(framing)
        moving = (separation > 0.5 or abs(framing.distance - self.distance) > 0.1
                  or abs(framing.focus - self.focus) > 0.01)
        self.elapsed = 0.0
        if not moving:
            self.target = framing
            self.duration = 0.0
            return 0.0
        self._settle_sway()
        self.target = framing
        self.origin = (self.latitude, self.longitude, self.distance, self.focus)
        self.turn = (framing.longitude - self.longitude + 180.0) % 360.0 - 180.0
        self.lift = min(self.highest_lift, self.lift_per_degree * separation)
        self.duration = min(self.longest_glide, self.base_seconds + self.seconds_per_quarter_turn * separation / 90.0)
        return self.duration

    def update(self, dt):
        if self.arrived:
            self.longitude += self.target.drift * dt
            if self.target.sway > 0.0:
                self.sway_time += dt
                self.sway_weight = min(1.0, self.sway_weight + dt / self.sway_ramp_seconds)
            return
        self.elapsed = min(self.duration, self.elapsed + dt)
        raw = self.elapsed / self.duration
        eased = raw * raw * (3.0 - 2.0 * raw)
        latitude, longitude, distance, focus = self.origin
        self.latitude = latitude + (self.target.latitude - latitude) * eased
        self.longitude = longitude + self.turn * eased
        self.distance = distance + (self.target.distance - distance) * eased + self.lift * math.sin(math.pi * raw)
        self.focus = focus + (self.target.focus - focus) * eased

    def elevation(self):
        return self.latitude - self.view_offset
