import math


class PathSample:
    def __init__(self, x, z, normal_x, normal_z, distance):
        self.x = x
        self.z = z
        self.normal_x = normal_x
        self.normal_z = normal_z
        self.distance = distance

    def offset(self, amount, height):
        return self.x + self.normal_x * amount, height, self.z + self.normal_z * amount


class RoadPath:
    """Straight centre line from `start` to `end` (x, z), sampled every `step`.
    Sample normals point to the left of the direction of travel."""

    def __init__(self, start, end, step=4.0):
        self.samples = []
        (start_x, start_z), (end_x, end_z) = start, end
        length = math.hypot(end_x - start_x, end_z - start_z)
        direction_x, direction_z = (end_x - start_x) / length, (end_z - start_z) / length
        count = max(1, int(math.ceil(length / step)))
        for index in range(count + 1):
            blend = index / count
            self._append(start_x + (end_x - start_x) * blend, start_z + (end_z - start_z) * blend,
                         direction_x, direction_z)

    def _append(self, x, z, direction_x, direction_z):
        distance = 0.0
        if self.samples:
            previous = self.samples[-1]
            distance = previous.distance + math.hypot(x - previous.x, z - previous.z)
        self.samples.append(PathSample(x, z, direction_z, -direction_x, distance))

    def length(self):
        return self.samples[-1].distance

    def point_at(self, distance):
        for previous, current in zip(self.samples, self.samples[1:]):
            if current.distance >= distance:
                span = current.distance - previous.distance
                blend = (distance - previous.distance) / span if span else 0.0
                return PathSample(previous.x + (current.x - previous.x) * blend,
                                  previous.z + (current.z - previous.z) * blend,
                                  previous.normal_x + (current.normal_x - previous.normal_x) * blend,
                                  previous.normal_z + (current.normal_z - previous.normal_z) * blend,
                                  distance)
        return self.samples[-1]


class RoadArm:
    """Straight road leaving the junction centre along `direction`.
    Positive offsets lie to the side its path normals point to."""

    def __init__(self, center, direction, length, step=4.0):
        direction_length = math.hypot(*direction)
        self.center = center
        self.direction = (direction[0] / direction_length, direction[1] / direction_length)
        self.normal = (self.direction[1], -self.direction[0])
        self.length = length
        self.path = RoadPath(center, self.point(length, 0.0)[::2], step)

    def point(self, along, offset, height=0.0):
        return (self.center[0] + self.direction[0] * along + self.normal[0] * offset,
                height,
                self.center[1] + self.direction[1] * along + self.normal[1] * offset)


class Corner:
    """Where the +`offset` side of `first` meets the -`offset` side of
    `second` (the next arm turning towards first.normal): a mitred joint."""

    def __init__(self, first, second, offset):
        (ax, az), (bx, bz) = first.direction, second.direction
        (nax, naz), (nbx, nbz) = first.normal, second.normal
        # first.center + t*a + offset*na == second.center + u*b - offset*nb
        right_x, right_z = -offset * (nax + nbx), -offset * (naz + nbz)
        determinant = ax * -bz - (-bx) * az
        self.first_along = (right_x * -bz - (-bx) * right_z) / determinant
        self.second_along = (ax * right_z - az * right_x) / determinant
        x, _, z = first.point(self.first_along, offset)
        self.x, self.z = x, z

    def at(self, height):
        return self.x, height, self.z


class YJunction:
    """Y-shaped crossroad centred in front of the library's west corner: the
    front street runs east, the north street runs north, and the branch
    leaves south-west at `branch_angle` degrees off the straight line.
    Arms are listed in turning order, so each consecutive pair (wrapping
    around) bounds one wedge; the first wedge (east -> north) is the
    library's plaza."""

    def __init__(self, center=(-13.0, 22.0), half_width=5.0, branch_angle=30.0, east_length=313.0,
                 north_length=322.0, branch_length=250.0):
        angle = math.radians(branch_angle)
        self.center = center
        self.half_width = half_width
        self.east = RoadArm(center, (1.0, 0.0), east_length)
        self.north = RoadArm(center, (0.0, -1.0), north_length)
        self.branch = RoadArm(center, (-math.cos(angle), math.sin(angle)), branch_length)
        self.arms = (self.east, self.north, self.branch)

    def wedges(self):
        return tuple(zip(self.arms, self.arms[1:] + self.arms[:1]))


class StreetPalette:
    def __init__(self):
        self.ground = (0.50, 0.52, 0.45)
        self.asphalt = (0.29, 0.30, 0.32)
        self.marking = (0.92, 0.92, 0.88)
        self.sidewalk = (0.74, 0.72, 0.70)
        self.plaza = (0.80, 0.73, 0.68)
        self.curb = (0.64, 0.64, 0.62)
        self.grass = (0.38, 0.55, 0.26)
        self.fence = (0.74, 0.76, 0.78)
        self.lamp = (0.56, 0.58, 0.61)
        self.lamp_head = (0.90, 0.90, 0.88)


class LampPost:
    def __init__(self, x, z, arm_x, arm_z, ground, palette, height=8.4, reach=1.8):
        self.x = x
        self.z = z
        self.arm_x = arm_x
        self.arm_z = arm_z
        self.ground = ground
        self.palette = palette
        self.height = height
        self.reach = reach

    def draw(self, shapes):
        palette = self.palette
        shapes.cylinder(self.x, self.ground, self.z, 0.14, 0.08, self.height, palette.lamp, 10)
        shapes.box(self.x - 0.2, self.ground, self.z - 0.2, self.x + 0.2, self.ground + 0.6, self.z + 0.2,
                   palette.lamp)
        start = (self.x, self.ground + self.height - 0.4, self.z)
        tip = (self.x + self.arm_x * self.reach, self.ground + self.height, self.z + self.arm_z * self.reach)
        shapes.beam(start, tip, 0.08, palette.lamp)
        shapes.box(tip[0] - 0.38, tip[1] - 0.14, tip[2] - 0.22, tip[0] + 0.38, tip[1] + 0.02, tip[2] + 0.22,
                   palette.lamp_head)


class Fence:
    def __init__(self, points, color, height=1.1, baluster_spacing=0.2):
        self.points = points
        self.color = color
        self.height = height
        self.baluster_spacing = baluster_spacing

    def draw(self, shapes):
        for start, end in zip(self.points, self.points[1:]):
            for level in (0.3, self.height - 0.05):
                shapes.beam((start[0], start[1] + level, start[2]), (end[0], end[1] + level, end[2]), 0.05,
                            self.color)
            shapes.box(start[0] - 0.05, start[1], start[2] - 0.05, start[0] + 0.05, start[1] + self.height + 0.05,
                       start[2] + 0.05, self.color)
            span = math.hypot(end[0] - start[0], end[2] - start[2])
            count = max(1, int(span / self.baluster_spacing))
            for index in range(1, count):
                blend = index / count
                x = start[0] + (end[0] - start[0]) * blend
                z = start[2] + (end[2] - start[2]) * blend
                shapes.box(x - 0.012, start[1] + 0.12, z - 0.012, x + 0.012, start[1] + self.height - 0.05, z + 0.012,
                           self.color)


class StreetScape:
    def __init__(self, junction, paving_texture):
        self.junction = junction
        self.paving_texture = paving_texture
        self.palette = StreetPalette()
        self.half_width = junction.half_width
        self.sidewalk_width = 6.0
        self.curb = 0.15
        self.block_limit_x = 130.0
        self.block_limit_z = -100.0
        center_x, center_z = junction.center
        plaza_wedge, *sidewalk_wedges = junction.wedges()
        self.plaza_wedge = plaza_wedge
        self.sidewalk_wedges = tuple(sidewalk_wedges)
        self.verge = RoadPath((center_x + self.half_width, center_z), (140.0, center_z))
        self.fence = Fence(tuple(sample.offset(8.9, self.curb) for sample in self.verge.samples), self.palette.fence)
        self.lamps = self._create_lamps()

    def _create_lamps(self):
        palette = self.palette
        center_x, center_z = self.junction.center
        branch = self.junction.branch
        lamps = [LampPost(x, center_z - 6.8, 0.0, 1.0, self.curb, palette) for x in (14.0, 42.0, 70.0, 98.0, 126.0)]
        lamps.append(LampPost(center_x, center_z + 6.8, 0.0, -1.0, self.curb, palette))
        lamps.extend(LampPost(center_x + 6.8, z, -1.0, 0.0, self.curb, palette) for z in (-18.0, -48.0, -78.0, -108.0))
        lamps.extend(LampPost(center_x - 9.5, z, 1.0, 0.0, self.curb, palette) for z in (-30.0, -70.0, -110.0))
        for along in (30.0, 60.0, 90.0):
            x, _, z = branch.point(along, 6.8)
            lamps.append(LampPost(x, z, -branch.normal[0], -branch.normal[1], self.curb, palette))
        return lamps

    def draw(self, shapes):
        palette = self.palette
        half, sidewalk = self.half_width, self.sidewalk_width
        self._draw_ground(shapes)
        self._draw_block(shapes)
        for arm in self.junction.arms:
            self._draw_band(shapes, self._straight_pairs(arm, -half, half, 0.05), palette.asphalt, False)
        middle = [Corner(first, second, half).at(0.05) for first, second in self.junction.wedges()]
        shapes.polygon(middle, palette.asphalt, (0.0, 1.0, 0.0))
        for first, second in self.sidewalk_wedges:
            for arm, side in ((first, 1.0), (second, -1.0)):
                self._draw_band(shapes, self._mitred_pairs(first, second, arm, side, half, half + sidewalk, self.curb),
                                palette.sidewalk, True)
                self._draw_curb(shapes, first, second, arm, side, half, -1.0)
                self._draw_curb(shapes, first, second, arm, side, half + sidewalk, 1.0)
        first, second = self.plaza_wedge
        for arm, side in ((first, 1.0), (second, -1.0)):
            self._draw_curb(shapes, first, second, arm, side, half, -1.0)
        self._draw_band(shapes, [(sample.offset(half + 0.25, self.curb + 0.02), sample.offset(half + 3.7, self.curb + 0.02))
                                 for sample in self.verge.samples], palette.grass, False)
        self._draw_markings(shapes)
        self._draw_crosswalk(shapes)
        self._draw_parking(shapes)
        self.fence.draw(shapes)
        for lamp in self.lamps:
            lamp.draw(shapes)

    def _draw_ground(self, shapes):
        extent = 700.0
        shapes.polygon(((-extent, 0.0, extent), (extent, 0.0, extent), (extent, 0.0, -extent), (-extent, 0.0, -extent)),
                       self.palette.ground, (0.0, 1.0, 0.0))
        lawn = ((6.0, 0.03, 33.2), (320.0, 0.03, 33.2), (320.0, 0.03, 160.0), (6.0, 0.03, 160.0))
        shapes.polygon(lawn, self.palette.grass, (0.0, 1.0, 0.0))

    def _draw_block(self, shapes):
        """Paved plaza in the corner between the north street and the east arm."""
        corner = Corner(*self.plaza_wedge, self.half_width)
        edge = ((corner.x, self.curb, self.block_limit_z), (corner.x, self.curb, corner.z),
                (self.block_limit_x, self.curb, corner.z), (self.block_limit_x, self.curb, self.block_limit_z))
        with shapes.textured(self.paving_texture):
            shapes.polygon(edge, self.palette.plaza, (0.0, 1.0, 0.0), [(x / 2.5, z / 2.5) for x, _, z in edge])

    def _straight_pairs(self, arm, inner, outer, height):
        return [(sample.offset(inner, height), sample.offset(outer, height)) for sample in arm.path.samples]

    def _mitred_pairs(self, first, second, arm, side, inner, outer, height):
        """Band between two offsets on one side of `arm`, its end at the
        junction cut along the mitre shared with the neighbouring arm."""
        inner_corner, outer_corner = Corner(first, second, inner), Corner(first, second, outer)
        along_of = (lambda corner: corner.first_along) if arm is first else (lambda corner: corner.second_along)
        start = max(along_of(inner_corner), along_of(outer_corner))
        pairs = [(inner_corner.at(height), outer_corner.at(height))]
        for sample in arm.path.samples:
            if sample.distance > start:
                pairs.append((sample.offset(side * inner, height), sample.offset(side * outer, height)))
        return pairs

    def _draw_band(self, shapes, pairs, color, textured):
        uvs = [((first[0] / 2.5, first[2] / 2.5), (second[0] / 2.5, second[2] / 2.5)) for first, second in pairs]
        with shapes.textured(self.paving_texture if textured else None):
            shapes.strip(pairs, [(0.0, 1.0, 0.0)] * len(pairs), color, uvs if textured else None)

    def _draw_curb(self, shapes, first, second, arm, side, offset, facing):
        """Curb along `offset` on one side of `arm`; facing -1 looks back at
        the road, +1 away from it."""
        line = [inner for inner, _ in self._mitred_pairs(first, second, arm, side, offset, offset, 0.0)]
        pairs = [((x, 0.0, z), (x, self.curb, z)) for x, _, z in line]
        normal = (arm.normal[0] * side * facing, 0.0, arm.normal[1] * side * facing)
        shapes.strip(pairs, [normal] * len(pairs), self.palette.curb)

    def _draw_markings(self, shapes):
        """Edge lines mitre at the corners like the curbs; centre dashes start
        just outside the junction on every arm."""
        for first, second in self.junction.wedges():
            for arm, side in ((first, 1.0), (second, -1.0)):
                self._draw_band(shapes, self._mitred_pairs(first, second, arm, side, 4.45, 4.6, 0.07),
                                self.palette.marking, False)
        crossing_z = (-1.0, 7.5)
        for arm in self.junction.arms:
            distance = self.half_width + 1.0
            while distance < arm.path.length() - 3.0:
                start = arm.path.point_at(distance)
                end = arm.path.point_at(distance + 3.0)
                if not (arm is self.junction.north and crossing_z[0] < start.z < crossing_z[1]):
                    self._draw_dash(shapes, start, end)
                distance += 6.0

    def _draw_dash(self, shapes, start, end):
        width = 0.08
        quad = (start.offset(-width, 0.075), start.offset(width, 0.075), end.offset(width, 0.075),
                end.offset(-width, 0.075))
        shapes.polygon(quad, self.palette.marking, (0.0, 1.0, 0.0))

    def _draw_crosswalk(self, shapes):
        left = self.junction.center[0] - self.half_width + 0.5
        for index in range(9):
            x = left + index * 1.0
            shapes.box(x, 0.05, 1.5, x + 0.5, 0.07, 5.5, self.palette.marking)

    def _draw_parking(self, shapes):
        for index in range(13):
            x = 58.0 + index * 2.7
            for near, far in ((-5.0, 0.0), (-15.0, -10.0)):
                shapes.box(x, self.curb, far, x + 0.12, self.curb + 0.015, near, self.palette.marking)
