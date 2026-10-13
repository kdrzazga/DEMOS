import math

from demos.pixeloveole3.logo_phases import HoldPhase, LogoShowPhase


class EnterHallPhase(LogoShowPhase):

    def __init__(self, show, duration, fade_seconds=1.0, flight_seconds=5.0, eye=(2.6, 2.3, -5.5),
                 start=(-4.6, 1.6, -9.5), waypoints=((-3.2, 1.7, -9.5), (-2.2, 1.9, -10.0)),
                 circle_center=(-1.2, 2.1, -10.8), circle_radius=1.1, grow_share=0.6):
        super().__init__(show, duration)
        self.fade_seconds = fade_seconds
        self.grow_share = grow_share
        self.flight_seconds = flight_seconds
        self.view = (eye, circle_center)
        self.start = start
        self.waypoints = waypoints
        self.circle = (circle_center, circle_radius, self.camera_right(eye, circle_center))

    @staticmethod
    def camera_right(eye, target):
        look_x, look_z = target[0] - eye[0], target[2] - eye[2]
        length = math.hypot(look_x, look_z) or 1.0
        return -look_z / length, 0.0, look_x / length

    def begin(self, handover):
        super().begin(handover)
        self.show.enter_hall(self.view, self.fade_seconds)
        self.show.fly_invader_into_hall(self.start, self.waypoints, self.flight_seconds, self.circle,
                                        self.grow_share)


def build_stage2_phases(show):
    return [
        EnterHallPhase(show, 8.0),
        HoldPhase(show, 1.0),
    ]
