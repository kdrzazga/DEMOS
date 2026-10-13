import math

from lib.demo_phases import CameraInterpolationHelper


def subtract(first, second):
    return tuple(a - b for a, b in zip(first, second))


def dot(first, second):
    return sum(a * b for a, b in zip(first, second))


def cross(first, second):
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def normalize(vector):
    length = math.sqrt(dot(vector, vector)) or 1.0
    return tuple(component / length for component in vector)


class CameraFrame:
    """Orthonormal basis of a gluLookAt camera, to move points between world
    and camera space (x right, y up, z = depth in front of the eye)."""

    def __init__(self, eye, target, up=(0.0, 1.0, 0.0)):
        self.eye = eye
        self.forward = normalize(subtract(target, eye))
        self.right = normalize(cross(self.forward, up))
        self.up = cross(self.right, self.forward)

    def to_camera(self, point):
        offset = subtract(point, self.eye)
        return dot(offset, self.right), dot(offset, self.up), dot(offset, self.forward)

    def to_world(self, local):
        return tuple(self.eye[axis] + self.right[axis] * local[0] + self.up[axis] * local[1]
                     + self.forward[axis] * local[2] for axis in range(3))


def catmull_rom(before, start, end, after, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * (2.0 * p1 + (p2 - p0) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                        + (3.0 * p1 - p0 - 3.0 * p2 + p3) * t3)
                 for p0, p1, p2, p3 in zip(before, start, end, after))


def spline_point(points, progress):
    """Point at `progress` (0..1) along a Catmull-Rom spline through `points`.
    Time is shared out by the square root of each leg's length, so short
    legs are not rushed through."""
    weights = [math.sqrt(math.dist(start, end)) for start, end in zip(points, points[1:])]
    remaining = progress * sum(weights)
    for index, weight in enumerate(weights):
        if remaining <= weight or index == len(weights) - 1:
            local = min(1.0, remaining / weight) if weight else 1.0
            before = points[max(index - 1, 0)]
            after = points[min(index + 2, len(points) - 1)]
            return catmull_rom(before, points[index], points[index + 1], after, local)
        remaining -= weight
    return points[-1]


def face_towards(part, eye):
    dx, dy, dz = subtract(eye, (part.x, part.y, part.z))
    part.yaw = math.degrees(math.atan2(dx, dz))
    part.pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))


class InvaderFlight:
    """Takes a part out of the logo overlay into the library world and flies
    it along `waypoints` (library coordinates), then on to `destination`, or
    back where it came from when there is none.

    The trip starts (and a return trip ends) at the library-world point that
    shows exactly where the part sits in the overlay: same spot on screen,
    same size, since depth is rescaled by the ratio of the two cameras'
    fields of view. Time is
    shared out by the square root of each leg's length, so the short legs
    through the portico are flown slowly enough to be seen. The part keeps
    facing the library camera; the camera itself is left alone."""

    def __init__(self, show, part, waypoints, duration, destination=None):
        self.show = show
        self.part = part
        self.waypoints = tuple(waypoints)
        self.destination = destination
        self.duration = duration
        self.elapsed = 0.0
        self.overlay_position = (part.x, part.y, part.z)
        self.done = False

    def anchor(self):
        """Library-world point where the part appears at its overlay position."""
        stage = self.show.stage
        logo_camera = CameraFrame(*stage.camera_view(self.show.elapsed))
        library_camera = CameraFrame(*self.show.current_library_view())
        depth_scale = (math.tan(math.radians(stage.field_of_view) / 2.0)
                       / math.tan(math.radians(self.show.library.field_of_view) / 2.0))
        right, up, depth = logo_camera.to_camera(self.overlay_position)
        return library_camera.to_world((right, up, depth * depth_scale)), library_camera.eye

    @property
    def returns(self):
        return self.destination is None

    def update(self, seconds):
        self.elapsed += seconds
        progress = CameraInterpolationHelper.smooth(self.elapsed / self.duration)
        anchor, eye = self.anchor()
        end = anchor if self.returns else self.destination
        self.part.x, self.part.y, self.part.z = spline_point((anchor, *self.waypoints, end), progress)
        face_towards(self.part, eye)
        self.done = self.elapsed >= self.duration

    def land(self):
        """Put the part back into overlay coordinates where it took off."""
        self.part.x, self.part.y, self.part.z = self.overlay_position
        self.part.yaw = self.part.pitch = 0.0


class WorldOrbit:
    """Circles a part in the library world, in the vertical plane z = centre z,
    counter-clockwise as seen from the front, starting where the part is and
    easing its speed in; the part keeps facing the camera."""

    def __init__(self, part, center, radius, period_seconds=10.0, ramp_seconds=2.0, direction=1.0,
                 across=(1.0, 0.0, 0.0)):
        self.part = part
        self.center = center
        self.radius = radius
        self.direction = direction
        self.across = across
        offset = subtract((part.x, part.y, part.z), center)
        self.angle = math.atan2(offset[1], dot(offset, across))
        self.angular_speed = 2.0 * math.pi / period_seconds
        self.ramp_seconds = ramp_seconds
        self.elapsed = 0.0
        self.travelled = 0.0

    @property
    def revolutions(self):
        return self.travelled / (2.0 * math.pi)

    def update(self, seconds, eye):
        self.elapsed += seconds
        step = self.angular_speed * min(1.0, self.elapsed / self.ramp_seconds) * seconds
        self.angle += step * self.direction
        self.travelled += step
        sideways = self.radius * math.cos(self.angle)
        self.part.x = self.center[0] + self.across[0] * sideways
        self.part.y = self.center[1] + self.radius * math.sin(self.angle)
        self.part.z = self.center[2] + self.across[2] * sideways
        face_towards(self.part, eye)


class WorldFlight:
    """Flies a part already in the library world from where it is through
    `waypoints`, shrinking it away over the last `shrink_share` of the trip
    (so it vanishes into the last waypoint); it keeps facing the camera."""

    def __init__(self, part, waypoints, duration, shrink_share=0.3, grow_share=0.0):
        self.part = part
        self.points = ((part.x, part.y, part.z), *waypoints)
        self.duration = duration
        self.shrink_share = shrink_share
        self.grow_share = grow_share
        self.elapsed = 0.0
        self.done = False

    def update(self, seconds, eye):
        self.elapsed += seconds
        progress = CameraInterpolationHelper.smooth(self.elapsed / self.duration)
        self.part.x, self.part.y, self.part.z = spline_point(self.points, progress)
        face_towards(self.part, eye)
        scale = 1.0
        if self.grow_share:
            scale = min(scale, progress / self.grow_share)
        if self.shrink_share:
            scale = min(scale, (1.0 - progress) / self.shrink_share)
        self.part.scale = scale
        self.done = self.elapsed >= self.duration
