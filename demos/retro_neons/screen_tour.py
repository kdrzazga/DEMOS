import math

from demos.retro_neons.flight import FlightPath
from lib.vector3 import Vector3


class ScreenView:

    def __init__(self, corners, normal):
        bottom_left, bottom_right, top_right, top_left = corners
        self.center = (bottom_left + top_right) * 0.5
        self.normal = normal
        self.width = (bottom_right - bottom_left).length()
        self.height = (top_left - bottom_left).length()
        self.across = (bottom_right - bottom_left).normalized()
        self.upward = (top_left - bottom_left).normalized()

    def distance_filling(self, share_of_view, field_of_view, view_aspect):
        half_view = math.tan(math.radians(field_of_view / 2.0))
        distance_fitting_height = self.height / 2.0 / half_view
        distance_fitting_width = self.width / 2.0 / (half_view * view_aspect)
        return max(distance_fitting_height, distance_fitting_width) / share_of_view

    def is_hidden_by(self, obstacle_point, eye, margin):
        toward_screen = (self.center - eye).dot(self.normal)
        toward_obstacle = (obstacle_point - eye).dot(self.normal)
        if toward_obstacle >= 0.0 or toward_obstacle <= toward_screen:
            return False
        on_screen_plane = eye + (obstacle_point - eye) * (toward_screen / toward_obstacle)
        from_center = on_screen_plane - self.center
        return (abs(from_center.dot(self.across)) < self.width / 2.0 + margin
                and abs(from_center.dot(self.upward)) < self.height / 2.0 + margin)


class LampObstacles:

    def __init__(self, street_lamps):
        self.sample_spacing = 0.5
        self.points = []
        for base, arm_direction in street_lamps.lamps:
            pole_top = base + Vector3(0.0, street_lamps.pole_height, 0.0)
            self.points.extend(self._points_between(base, pole_top))
            self.points.extend(self._points_between(pole_top, pole_top + arm_direction * street_lamps.arm_reach))

    def _points_between(self, start, end):
        step_count = max(1, math.ceil((end - start).length() / self.sample_spacing))
        return [start + (end - start) * (step / step_count) for step in range(step_count + 1)]

    def nearest_point_to(self, position):
        return min(self.points, key=lambda point: (point - position).length())

    def distance_to(self, position):
        return (self.nearest_point_to(position) - position).length()

    def hide(self, view, eye, margin):
        return any(view.is_hidden_by(point, eye, margin) for point in self.points)


class TourKey:

    def __init__(self, seconds, eye, target):
        self.seconds = seconds
        self.eye = eye
        self.target = target

    def values(self):
        return (*self.eye, *self.target)


class ScreenTour:

    def __init__(self, balcony_eye, balcony_target, c64_view, credits_view, scroll_view, lamp_obstacles,
                 field_of_view, view_aspect):
        self.lamp_obstacles = lamp_obstacles
        self.field_of_view = field_of_view
        self.view_aspect = view_aspect
        self.wide_share_of_view = 0.5
        self.close_share_of_view = 0.95
        self.c64_arrival_seconds = 5.0
        self.c64_close_seconds = 8.0
        self.c64_wide_again_seconds = 10.5
        self.credits_close_seconds = 15.0
        self.credits_wide_again_seconds = 17.5
        self.scroll_close_seconds = 22.0
        self.sequence_seconds = 25.0
        self.return_seconds = 4.0
        self.scroll_close_share_of_view = 0.6
        self.scroll_drift_share_of_view = 0.66
        self.viewpoint_lamp_clearance = 2.5
        self.screen_edge_lamp_margin = 0.8
        self.viewpoint_rise_step = 0.5
        self.viewpoint_highest_rise = 14.0
        self.viewpoint_side_step = 0.75
        self.viewpoint_widest_side_step = 8.0
        self.flight_lamp_clearance = 1.8
        self.flight_check_step_seconds = 0.1
        self.detour_overshoot = 0.6
        self.most_detours = 16
        self.closest_detour_to_key_seconds = 0.35
        self.keys = [TourKey(0.0, balcony_eye, balcony_target),
                     self._key(self.c64_arrival_seconds, c64_view, self.wide_share_of_view),
                     self._key(self.c64_close_seconds, c64_view, self.close_share_of_view),
                     self._key(self.c64_wide_again_seconds, c64_view, self.wide_share_of_view)]
        if credits_view is not None:
            self.keys.append(self._key(self.credits_close_seconds, credits_view, self.close_share_of_view))
            self.keys.append(self._key(self.credits_wide_again_seconds, credits_view, self.wide_share_of_view))
        self.keys.append(self._key(self.scroll_close_seconds, scroll_view, self.scroll_close_share_of_view))
        self.keys.append(self._key(self.sequence_seconds, scroll_view, self.scroll_drift_share_of_view))
        self.keys.append(TourKey(self.sequence_seconds + self.return_seconds, balcony_eye, balcony_target))
        self.path = FlightPath(self.keys)
        self._bend_flight_around_lamps()

    def _key(self, seconds, view, share_of_view):
        distance = view.distance_filling(share_of_view, self.field_of_view, self.view_aspect)
        return TourKey(seconds, self._viewpoint_clear_of_lamps(view, distance), view.center)

    def _viewpoint_clear_of_lamps(self, view, distance):
        straight_ahead = view.center + view.normal * distance
        best_viewpoint = straight_ahead
        smallest_shift = None
        for rise in self._steps_up_to(self.viewpoint_highest_rise, self.viewpoint_rise_step):
            for side_shift in self._steps_either_way(self.viewpoint_widest_side_step, self.viewpoint_side_step):
                shift = rise + abs(side_shift)
                if smallest_shift is not None and shift >= smallest_shift:
                    continue
                shifted = straight_ahead + Vector3(0.0, rise, 0.0) + view.across * side_shift
                viewpoint = view.center + (shifted - view.center).normalized() * distance
                if self._viewpoint_is_clear(view, viewpoint):
                    best_viewpoint = viewpoint
                    smallest_shift = shift
        return best_viewpoint

    def _viewpoint_is_clear(self, view, viewpoint):
        return (self.lamp_obstacles.distance_to(viewpoint) >= self.viewpoint_lamp_clearance
                and not self.lamp_obstacles.hide(view, viewpoint, self.screen_edge_lamp_margin))

    @staticmethod
    def _steps_up_to(limit, step):
        return [index * step for index in range(int(limit / step) + 1)]

    def _steps_either_way(self, limit, step):
        one_way = self._steps_up_to(limit, step)
        return one_way + [-shift for shift in one_way[1:]]

    def _bend_flight_around_lamps(self):
        for _ in range(self.most_detours):
            detour = self._first_detour_needed()
            if detour is None:
                return
            self.keys.append(detour)
            self.keys.sort(key=lambda key: key.seconds)
            self.path = FlightPath(self.keys)

    def _first_detour_needed(self):
        key_times = [key.seconds for key in self.keys]
        step_count = int(self.duration / self.flight_check_step_seconds)
        for step in range(1, step_count):
            seconds = step * self.flight_check_step_seconds
            if min(abs(seconds - key_time) for key_time in key_times) < self.closest_detour_to_key_seconds:
                continue
            eye, target = self.eye_and_target(seconds)
            nearest_lamp_point = self.lamp_obstacles.nearest_point_to(eye)
            away_from_lamp = eye - nearest_lamp_point
            if away_from_lamp.length() < self.flight_lamp_clearance:
                pushed_eye = nearest_lamp_point + self._direction_away(away_from_lamp) * (self.flight_lamp_clearance
                                                                                         + self.detour_overshoot)
                return TourKey(seconds, pushed_eye, target)
        return None

    @staticmethod
    def _direction_away(away_from_lamp):
        if away_from_lamp.length() < 0.01:
            return Vector3(0.0, 1.0, 0.0)
        return away_from_lamp.normalized()

    @property
    def duration(self):
        return self.path.duration

    def eye_and_target(self, seconds):
        eye_x, eye_y, eye_z, target_x, target_y, target_z = self.path.sample(seconds)
        return Vector3(eye_x, eye_y, eye_z), Vector3(target_x, target_y, target_z)
