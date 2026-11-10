import math

from OpenGL.GLU import gluLookAt

from lib.vector3 import Vector3


class CameraKey:

    def __init__(self, seconds, eye, yaw_degrees, pitch_degrees):
        self.seconds = seconds
        self.eye = eye
        self.yaw_degrees = yaw_degrees
        self.pitch_degrees = pitch_degrees

    def values(self):
        return (self.eye.x, self.eye.y, self.eye.z, self.yaw_degrees, self.pitch_degrees)


class FlightPath:

    def __init__(self, keys):
        self.times = [key.seconds for key in keys]
        self.points = [key.values() for key in keys]
        self.tangents = self._tangents()

    @property
    def duration(self):
        return self.times[-1]

    def _tangents(self):
        resting = tuple(0.0 for _ in self.points[0])
        tangents = [resting]
        for index in range(1, len(self.points) - 1):
            span = self.times[index + 1] - self.times[index - 1]
            tangents.append(tuple((after - before) / span
                                  for before, after in zip(self.points[index - 1], self.points[index + 1])))
        tangents.append(resting)
        return tangents

    def sample(self, seconds):
        seconds = min(max(seconds, self.times[0]), self.duration)
        index = 0
        while index < len(self.times) - 2 and seconds > self.times[index + 1]:
            index += 1
        span = self.times[index + 1] - self.times[index]
        share = (seconds - self.times[index]) / span
        squared = share * share
        cubed = squared * share
        start_weight = 2.0 * cubed - 3.0 * squared + 1.0
        start_slope_weight = (cubed - 2.0 * squared + share) * span
        end_weight = -2.0 * cubed + 3.0 * squared
        end_slope_weight = (cubed - squared) * span
        return tuple(start_weight * start + start_slope_weight * start_slope + end_weight * end
                     + end_slope_weight * end_slope
                     for start, start_slope, end, end_slope in zip(self.points[index], self.tangents[index],
                                                                   self.points[index + 1],
                                                                   self.tangents[index + 1]))


class FlightCamera:

    def __init__(self, path, landing_camera):
        self.path = path
        self.landing_camera = landing_camera
        self.look_distance = 50.0
        self.elapsed = 0.0
        self.flying = False

    @staticmethod
    def heading_of(direction):
        unit = direction.normalized()
        return math.degrees(math.atan2(unit.x, unit.z)), math.degrees(math.asin(unit.y))

    def take_off(self):
        self.flying = True

    @property
    def landed(self):
        return self.elapsed >= self.path.duration

    def update(self, seconds):
        if self.landed:
            self.landing_camera.update(seconds)
        elif self.flying:
            self.elapsed = min(self.elapsed + seconds, self.path.duration)

    def toggle_pause(self):
        self.landing_camera.toggle_pause()

    def eye(self):
        if self.landed:
            return self.landing_camera.eye()
        x, y, z, _, _ = self.path.sample(self.elapsed)
        return Vector3(x, y, z)

    def target(self):
        if self.landed:
            return self.landing_camera.target()
        _, _, _, yaw_degrees, pitch_degrees = self.path.sample(self.elapsed)
        yaw = math.radians(yaw_degrees)
        pitch = math.radians(pitch_degrees)
        direction = Vector3(math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch))
        return self.eye() + direction * self.look_distance

    def forward(self):
        return (self.target() - self.eye()).normalized()

    def right(self):
        return self.forward().cross(Vector3(0.0, 1.0, 0.0)).normalized()

    def up(self):
        return self.right().cross(self.forward()).normalized()

    def placement_matrix(self):
        backward = self.forward() * -1.0
        return (*self.right(), 0.0, *self.up(), 0.0, *backward, 0.0, *self.eye(), 1.0)

    def look(self):
        gluLookAt(*self.eye(), *self.target(), 0.0, 1.0, 0.0)
