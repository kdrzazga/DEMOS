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
    def __init__(self, west_x=-13.0, front_z=22.0, radius=14.0, north_z=-300.0, east_x=300.0, step=4.0,
                 arc_segments=24):
        self.west_x = west_x
        self.front_z = front_z
        self.radius = radius
        self.corner_x = west_x + radius
        self.corner_z = front_z - radius
        self.samples = []
        z = north_z
        while z < self.corner_z:
            self._append(west_x, z, 0.0, 1.0)
            z += step
        for index in range(arc_segments):
            angle = math.pi - (math.pi / 2.0) * index / arc_segments
            self._append(self.corner_x + radius * math.cos(angle), self.corner_z + radius * math.sin(angle),
                         math.sin(angle), -math.cos(angle))
        x = self.corner_x
        while x <= east_x:
            self._append(x, front_z, 1.0, 0.0)
            x += step

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

    def arc_point(self, angle, inset):
        radius = self.radius - inset
        return (self.corner_x + radius * math.cos(angle), self.corner_z + radius * math.sin(angle),
                -math.cos(angle), -math.sin(angle))


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
    def __init__(self, path, paving_texture):
        self.path = path
        self.paving_texture = paving_texture
        self.palette = StreetPalette()
        self.half_width = 5.0
        self.sidewalk_width = 6.0
        self.curb = 0.15
        self.block_limit_x = 130.0
        self.block_limit_z = -100.0
        self.front_samples = tuple(sample for sample in path.samples
                                   if -9.0 <= sample.x <= 140.0 and sample.z >= path.corner_z)
        self.fence = Fence(tuple(sample.offset(8.9, self.curb) for sample in self.front_samples), self.palette.fence)
        self.lamps = self._create_lamps()

    def _create_lamps(self):
        palette = self.palette
        path = self.path
        lamps = [LampPost(x, path.front_z - 6.8, 0.0, 1.0, self.curb, palette) for x in (14.0, 42.0, 70.0, 98.0, 126.0)]
        arc_x, arc_z, arm_x, arm_z = path.arc_point(math.pi * 0.75, 6.8)
        lamps.append(LampPost(arc_x, arc_z, -arm_x, -arm_z, self.curb, palette))
        lamps.extend(LampPost(path.west_x + 6.8, z, -1.0, 0.0, self.curb, palette) for z in (-18.0, -48.0, -78.0, -108.0))
        lamps.extend(LampPost(path.west_x - 9.5, z, 1.0, 0.0, self.curb, palette) for z in (-30.0, -70.0, -110.0))
        return lamps

    def draw(self, shapes):
        palette = self.palette
        samples = self.path.samples
        half = self.half_width
        self._draw_ground(shapes)
        self._draw_block(shapes)
        self._draw_ribbon(shapes, samples, -half, half, 0.05, palette.asphalt, False)
        self._draw_ribbon(shapes, samples, -half - self.sidewalk_width, -half, self.curb, palette.sidewalk, True)
        self._draw_curb(shapes, samples, half, -1.0)
        self._draw_curb(shapes, samples, -half, 1.0)
        self._draw_curb(shapes, samples, -half - self.sidewalk_width, -1.0)
        self._draw_ribbon(shapes, self.front_samples, half + 0.25, half + 3.7, self.curb + 0.02, palette.grass, False)
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
        edge = [sample.offset(self.half_width, self.curb) for sample in self.path.samples]
        edge = [point for point in edge if point[0] <= self.block_limit_x and point[2] >= self.block_limit_z]
        edge.append((edge[-1][0], self.curb, self.block_limit_z))
        with shapes.textured(self.paving_texture):
            shapes.polygon(edge, self.palette.plaza, (0.0, 1.0, 0.0), [(x / 2.5, z / 2.5) for x, _, z in edge])

    def _draw_ribbon(self, shapes, samples, inner, outer, height, color, textured):
        pairs = [(sample.offset(inner, height), sample.offset(outer, height)) for sample in samples]
        uvs = [((first[0] / 2.5, first[2] / 2.5), (second[0] / 2.5, second[2] / 2.5)) for first, second in pairs]
        with shapes.textured(self.paving_texture if textured else None):
            shapes.strip(pairs, [(0.0, 1.0, 0.0)] * len(pairs), color, uvs if textured else None)

    def _draw_curb(self, shapes, samples, offset, facing):
        pairs = [(sample.offset(offset, 0.0), sample.offset(offset, self.curb)) for sample in samples]
        normals = [(sample.normal_x * facing, 0.0, sample.normal_z * facing) for sample in samples]
        shapes.strip(pairs, normals, self.palette.curb)

    def _draw_markings(self, shapes):
        for offset in (4.45, -4.6):
            self._draw_ribbon(shapes, self.path.samples, offset, offset + 0.15, 0.07, self.palette.marking, False)
        distance = 0.0
        while distance < self.path.length() - 3.0:
            start = self.path.point_at(distance)
            end = self.path.point_at(distance + 3.0)
            if not (start.x < self.path.west_x + 1.0 and -1.0 < start.z < 7.5):
                self._draw_dash(shapes, start, end)
            distance += 6.0

    def _draw_dash(self, shapes, start, end):
        width = 0.08
        quad = (start.offset(-width, 0.075), start.offset(width, 0.075), end.offset(width, 0.075),
                end.offset(-width, 0.075))
        shapes.polygon(quad, self.palette.marking, (0.0, 1.0, 0.0))

    def _draw_crosswalk(self, shapes):
        left = self.path.west_x - self.half_width + 0.5
        for index in range(9):
            x = left + index * 1.0
            shapes.box(x, 0.05, 1.5, x + 0.5, 0.07, 5.5, self.palette.marking)

    def _draw_parking(self, shapes):
        for index in range(13):
            x = 58.0 + index * 2.7
            for near, far in ((-5.0, 0.0), (-15.0, -10.0)):
                shapes.box(x, self.curb, far, x + 0.12, self.curb + 0.015, near, self.palette.marking)
