import math

import numpy
from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps


def smoothstep(edge_start, edge_end, value):
    fraction = numpy.clip((value - edge_start) / (edge_end - edge_start), 0.0, 1.0)
    return fraction * fraction * (3.0 - 2.0 * fraction)


def hermite_profile(knots, values, samples):
    knots = numpy.asarray(knots, dtype=numpy.float64)
    values = numpy.asarray(values, dtype=numpy.float64)
    slopes = numpy.gradient(values, knots)
    segment = numpy.clip(numpy.searchsorted(knots, samples, side="right") - 1, 0, len(knots) - 2)
    span = knots[segment + 1] - knots[segment]
    local = (samples - knots[segment]) / span
    local_squared, local_cubed = local * local, local * local * local
    return ((2.0 * local_cubed - 3.0 * local_squared + 1.0) * values[segment]
            + (local_cubed - 2.0 * local_squared + local) * span * slopes[segment]
            + (-2.0 * local_cubed + 3.0 * local_squared) * values[segment + 1]
            + (local_cubed - local_squared) * span * slopes[segment + 1])


def quadratic_curve(start, control, end, count):
    start, control, end = numpy.asarray(start), numpy.asarray(control), numpy.asarray(end)
    steps = numpy.linspace(0.0, 1.0, count)[:, None]
    return (1.0 - steps) ** 2 * start + 2.0 * (1.0 - steps) * steps * control + steps ** 2 * end


class SharkBodyShape:

    def __init__(self):
        self.snout_x = 0.5
        self.body_span = 0.86
        self.knots = (0.0, 0.02, 0.06, 0.12, 0.20, 0.30, 0.40, 0.50, 0.62, 0.74, 0.86, 0.94, 1.0)
        self.half_heights = (0.0, 0.020, 0.043, 0.068, 0.090, 0.106, 0.111, 0.105, 0.085, 0.058, 0.032, 0.020, 0.016)
        self.half_widths = (0.0, 0.019, 0.038, 0.057, 0.074, 0.085, 0.087, 0.081, 0.064, 0.044, 0.027, 0.022, 0.020)
        self.centers = (0.012, 0.008, 0.002, -0.004, -0.008, -0.008, -0.006, -0.003, 0.0, 0.004, 0.008, 0.010, 0.012)
        self.belly_flattening = 0.9

    def x_at(self, along):
        return self.snout_x - along * self.body_span

    def along_at(self, x):
        return (self.snout_x - x) / self.body_span

    def section(self, along):
        along = numpy.asarray(along, dtype=numpy.float64)
        return (hermite_profile(self.knots, self.centers, along),
                numpy.maximum(hermite_profile(self.knots, self.half_heights, along), 0.0),
                numpy.maximum(hermite_profile(self.knots, self.half_widths, along), 0.0))

    def top_at(self, x):
        center, half_height, _ = self.section(self.along_at(x))
        return float(center + half_height)

    def bottom_at(self, x):
        center, half_height, _ = self.section(self.along_at(x))
        return float(center - half_height * self.belly_flattening)

    def girth_at(self, x):
        center, half_height, half_width = self.section(self.along_at(x))
        return float(center), float(half_height), float(half_width)


class SharkSkin:

    def __init__(self, shape, seed):
        self.shape = shape
        self.generator = numpy.random.default_rng(seed)
        self.columns = 512
        self.rows = 256
        self.top_color = numpy.array((0.27, 0.29, 0.30))
        self.flank_color = numpy.array((0.45, 0.45, 0.40))
        self.head_tint = numpy.array((0.50, 0.45, 0.33))
        self.belly_color = numpy.array((0.92, 0.92, 0.90))
        self.belly_shade = 0.12
        self.mottle_strength = 0.22
        self.freckle_density = 0.035
        self.freckle_darkness = 0.55
        self.boundary_knots = (0.0, 0.08, 0.18, 0.30, 0.45, 0.60, 0.75, 0.90, 1.0)
        self.boundary_levels = (0.66, 0.64, 0.60, 0.61, 0.57, 0.61, 0.56, 0.52, 0.50)
        self.boundary_ripples = ((7.0, 0.03), (19.0, 0.02), (43.0, 0.012), (97.0, 0.008))
        self.boundary_step_count = 96
        self.boundary_step_size = 0.02
        self.boundary_softness = 0.006
        self.gill_positions = (0.255, 0.278, 0.300, 0.322, 0.344)
        self.gill_span = (0.30, 0.72)
        self.gill_bow = 0.012
        self.gill_line = 0.0028
        self.gill_color = numpy.array((0.15, 0.15, 0.14))
        self.gill_fold_lift = 0.14
        self.eye_along = 0.088
        self.eye_level = 0.42
        self.eye_radius = 0.009
        self.eye_color = numpy.array((0.03, 0.03, 0.03))
        self.eye_rim_color = numpy.array((0.16, 0.15, 0.13))
        self.mouth_span = (0.055, 0.165)
        self.mouth_levels = (0.72, 0.63)
        self.mouth_line = 0.007
        self.mouth_color = numpy.array((0.13, 0.06, 0.06))
        self.gum_color = numpy.array((0.62, 0.38, 0.36))
        self.teeth_color = numpy.array((0.93, 0.91, 0.86))
        self.teeth_frequency = 650.0
        self.nostril_along = 0.035
        self.nostril_level = 0.56
        self.nostril_radius = 0.006
        self.snout_tip_darkening = 0.25
        self.along = numpy.linspace(0.0, 1.0, self.columns)[None, :]
        self.around = numpy.linspace(0.0, 2.0 * math.pi, self.rows, endpoint=False)[:, None]
        self.level = numpy.minimum(self.around, 2.0 * math.pi - self.around) / math.pi
        self.right_side = self.around < math.pi

    def smooth_noise(self, cells_around, cells_along):
        grid = self.generator.random((cells_around, cells_along + 1))
        around = numpy.linspace(0.0, cells_around, self.rows, endpoint=False)
        along = numpy.linspace(0.0, cells_along, self.columns)
        around_cell = numpy.floor(around).astype(int)
        along_cell = numpy.minimum(numpy.floor(along).astype(int), cells_along - 1)
        around_blend = smoothstep(0.0, 1.0, around - around_cell)[:, None]
        along_blend = smoothstep(0.0, 1.0, along - along_cell)[None, :]
        near_row, far_row = grid[around_cell], grid[(around_cell + 1) % cells_around]
        near = near_row[:, along_cell] * (1.0 - along_blend) + near_row[:, along_cell + 1] * along_blend
        far = far_row[:, along_cell] * (1.0 - along_blend) + far_row[:, along_cell + 1] * along_blend
        return near * (1.0 - around_blend) + far * around_blend

    def boundary_line(self):
        along = self.along[0]
        line = numpy.interp(along, self.boundary_knots, self.boundary_levels)
        for frequency, amplitude in self.boundary_ripples:
            line += amplitude * numpy.sin(2.0 * math.pi * frequency * along + self.generator.uniform(0.0, 2.0 * math.pi))
        steps = self.generator.uniform(-self.boundary_step_size, self.boundary_step_size, self.boundary_step_count)
        line += numpy.repeat(steps, -(-self.columns // self.boundary_step_count))[:self.columns]
        return line[None, :]

    def metric_offsets(self, along_center, level_center):
        _, half_height, half_width = self.shape.section(along_center)
        radius = float(half_height + half_width) / 2.0
        along_offset = (self.along - along_center) * self.shape.body_span
        level_offset = (self.level - level_center) * math.pi * radius
        return along_offset, level_offset

    def paint(self, colors, mask, color):
        colors[mask > 0.0] = (colors * (1.0 - mask[..., None]) + color * mask[..., None])[mask > 0.0]

    def base_colors(self):
        boundary = numpy.where(self.right_side, self.boundary_line(), self.boundary_line())
        whiteness = smoothstep(boundary - self.boundary_softness, boundary + self.boundary_softness, self.level)
        toward_boundary = numpy.clip(self.level / boundary, 0.0, 1.0) ** 1.5
        dark = self.top_color + (self.flank_color - self.top_color) * toward_boundary[..., None]
        head_weight = (1.0 - smoothstep(0.18, 0.45, self.along)) * toward_boundary
        dark = dark + (self.head_tint - dark) * head_weight[..., None] * 0.7
        mottle = 1.0 + self.mottle_strength * (self.smooth_noise(16, 40) - 0.5) + 0.1 * (self.smooth_noise(48, 120) - 0.5)
        dark = dark * mottle[..., None]
        freckles = (self.generator.random(self.level.shape) < self.freckle_density * (head_weight + 0.15)) * self.freckle_darkness
        dark = dark * (1.0 - freckles[..., None])
        belly = self.belly_color * (1.0 - self.belly_shade * numpy.abs(self.level - 1.0))[..., None]
        colors = dark * (1.0 - whiteness[..., None]) + belly * whiteness[..., None]
        snout = (1.0 - smoothstep(0.0, 0.06, self.along)) * self.snout_tip_darkening
        return colors * (1.0 - snout[..., None])

    def paint_gills(self, colors):
        low, high = self.gill_span
        inside = smoothstep(low - 0.02, low + 0.02, self.level) * (1.0 - smoothstep(high - 0.02, high + 0.02, self.level))
        bow = self.gill_bow * numpy.sin(numpy.clip((self.level - low) / (high - low), 0.0, 1.0) * math.pi)
        for position in self.gill_positions:
            offset = self.along - position - bow
            slit = (1.0 - smoothstep(0.0, self.gill_line, numpy.abs(offset))) * inside
            fold = (1.0 - smoothstep(0.0, self.gill_line, numpy.abs(offset - 2.0 * self.gill_line))) * inside
            colors *= (1.0 + self.gill_fold_lift * fold)[..., None]
            self.paint(colors, slit, self.gill_color)

    def paint_eye(self, colors):
        along_offset, level_offset = self.metric_offsets(self.eye_along, self.eye_level)
        distance = numpy.hypot(along_offset, level_offset)
        self.paint(colors, 1.0 - smoothstep(self.eye_radius, self.eye_radius * 1.5, distance), self.eye_rim_color)
        self.paint(colors, 1.0 - smoothstep(self.eye_radius * 0.75, self.eye_radius, distance), self.eye_color)
        along_offset, level_offset = self.metric_offsets(self.nostril_along, self.nostril_level)
        nostril = 1.0 - smoothstep(self.nostril_radius * 0.6, self.nostril_radius, numpy.hypot(along_offset * 0.5, level_offset))
        self.paint(colors, nostril * 0.8, self.eye_color)

    def paint_mouth(self, colors):
        start, end = self.mouth_span
        progress = numpy.clip((self.along - start) / (end - start), 0.0, 1.0)
        within = smoothstep(start - 0.004, start + 0.004, self.along) * (1.0 - smoothstep(end - 0.004, end + 0.004, self.along))
        line_level = self.mouth_levels[0] + (self.mouth_levels[1] - self.mouth_levels[0]) * progress ** 0.7
        offset = self.level - line_level
        gum = (1.0 - smoothstep(self.mouth_line, self.mouth_line * 1.8, numpy.abs(offset + self.mouth_line * 1.6))) * within
        teeth = gum * (numpy.sin(self.along * self.teeth_frequency) > 0.2)
        lips = (1.0 - smoothstep(self.mouth_line * 0.4, self.mouth_line, numpy.abs(offset))) * within
        self.paint(colors, gum, self.gum_color)
        self.paint(colors, teeth, self.teeth_color)
        self.paint(colors, lips, self.mouth_color)

    def pixels(self):
        colors = self.base_colors()
        self.paint_gills(colors)
        self.paint_eye(colors)
        self.paint_mouth(colors)
        return (numpy.clip(colors, 0.0, 1.0) * 255.0).astype(numpy.uint8)

    def upload(self):
        pixels = numpy.ascontiguousarray(self.pixels())
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, self.columns, self.rows, GL_RGB, GL_UNSIGNED_BYTE, pixels)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture


class FinBuilder:

    def __init__(self):
        self.half_thickness = 0.004
        self.tip_fade = 0.06
        self.positions = []
        self.normals = []
        self.colors = []

    @staticmethod
    def plane_normal(points):
        normal = numpy.zeros(3)
        for current, following in zip(points, numpy.roll(points, -1, axis=0)):
            normal += numpy.cross(current, following)
        length = numpy.linalg.norm(normal)
        return normal / length if length > 0.0 else numpy.array((0.0, 0.0, 1.0))

    def tinted(self, point, color, tip, tip_color):
        if tip is None:
            return color
        weight = max(0.0, 1.0 - numpy.linalg.norm(point - tip) / self.tip_fade)
        return color * (1.0 - weight) + tip_color * weight

    def add_fan(self, center, rim, first_side_color, second_side_color, tip=None, tip_color=None):
        center = numpy.asarray(center, dtype=numpy.float64)
        rim = numpy.asarray(rim, dtype=numpy.float64)
        normal = self.plane_normal(numpy.vstack((center[None, :], rim)))
        if normal[1] < 0.0 or (abs(normal[1]) < 1e-6 and normal[2] < 0.0):
            normal = -normal
        first_side_color, second_side_color = numpy.asarray(first_side_color), numpy.asarray(second_side_color)
        tip_color = None if tip_color is None else numpy.asarray(tip_color)
        tip = None if tip is None else numpy.asarray(tip, dtype=numpy.float64)
        for side, side_color in ((1.0, first_side_color), (-1.0, second_side_color)):
            lift = normal * self.half_thickness * side
            for current, following in zip(rim[:-1], rim[1:]):
                for point in (center, current, following):
                    self.positions.append(point + lift)
                    self.normals.append(normal * side)
                    self.colors.append(self.tinted(point, side_color, tip, tip_color))

    def arrays(self):
        return (numpy.array(self.positions, dtype=numpy.float32), numpy.array(self.normals, dtype=numpy.float32),
                numpy.array(self.colors, dtype=numpy.float32))


class SharkModel:

    def __init__(self, seed=5):
        self.shape = SharkBodyShape()
        self.rings = 72
        self.segments = 36
        self.dark_fin_color = (0.30, 0.31, 0.31)
        self.fin_top_color = (0.38, 0.38, 0.34)
        self.fin_belly_color = (0.86, 0.86, 0.84)
        self.fin_tip_color = (0.14, 0.14, 0.15)
        self.fin_edge_samples = 9
        self.texture = SharkSkin(self.shape, seed).upload()
        self.body_positions, self.body_normals, self.body_texture_points, self.body_indices = self.build_body()
        self.fin_positions, self.fin_normals, self.fin_colors = self.build_fins()

    def build_body(self):
        along = numpy.linspace(0.0, 1.0, self.rings)
        around = numpy.linspace(0.0, 2.0 * math.pi, self.segments + 1)
        center, half_height, half_width = self.shape.section(along)
        upward = numpy.cos(around)[None, :]
        flattening = numpy.where(upward < 0.0, self.shape.belly_flattening, 1.0)
        x = numpy.repeat(self.shape.x_at(along)[:, None], self.segments + 1, axis=1)
        y = center[:, None] + half_height[:, None] * upward * flattening
        z = half_width[:, None] * numpy.sin(around)[None, :]
        grid = numpy.stack((x, y, z), axis=-1)
        normals = self.grid_normals(grid, center)
        texture_points = numpy.stack(numpy.meshgrid(along, around / (2.0 * math.pi), indexing="ij"), axis=-1)
        indices = []
        width = self.segments + 1
        for ring in range(self.rings - 1):
            for segment in range(self.segments):
                corner = ring * width + segment
                indices.extend((corner, corner + width, corner + 1, corner + 1, corner + width, corner + width + 1))
        return (grid.reshape(-1, 3).astype(numpy.float32), normals.reshape(-1, 3).astype(numpy.float32),
                texture_points.reshape(-1, 2).astype(numpy.float32), numpy.array(indices, dtype=numpy.uint32))

    @staticmethod
    def grid_normals(grid, center):
        along_tangent = numpy.gradient(grid, axis=0)
        ring = grid[:, :-1]
        around_tangent = numpy.roll(ring, -1, axis=1) - numpy.roll(ring, 1, axis=1)
        around_tangent = numpy.concatenate((around_tangent, around_tangent[:, :1]), axis=1)
        normals = numpy.cross(along_tangent, around_tangent)
        outward = grid - numpy.stack((grid[..., 0], center[:, None] + 0.0 * grid[..., 1], 0.0 * grid[..., 2]), axis=-1)
        flip = numpy.sum(normals * outward, axis=-1) < 0.0
        normals[flip] = -normals[flip]
        lengths = numpy.linalg.norm(normals, axis=-1, keepdims=True)
        normals = numpy.where(lengths > 1e-9, normals / numpy.maximum(lengths, 1e-9), numpy.array((1.0, 0.0, 0.0)))
        normals[0, :] = (1.0, 0.0, 0.0)
        return normals

    def edge(self, start, control, end):
        return quadratic_curve(start, control, end, self.fin_edge_samples)

    def build_fins(self):
        fins = FinBuilder()
        self.add_dorsal_fins(fins)
        self.add_pectoral_fins(fins)
        self.add_pelvic_fins(fins)
        self.add_caudal_fin(fins)
        return fins.arrays()

    def add_dorsal_fins(self, fins):
        shape = self.shape
        front, rear = 0.05, -0.11
        front_point = (front, shape.top_at(front) - 0.01, 0.0)
        rear_point = (rear, shape.top_at(rear) - 0.01, 0.0)
        apex = (-0.115, shape.top_at(-0.03) + 0.165, 0.0)
        leading = self.edge(front_point, (-0.02, shape.top_at(-0.02) + 0.10, 0.0), apex)
        trailing = self.edge(apex, (-0.075, shape.top_at(-0.08) + 0.04, 0.0), rear_point)
        rim = numpy.vstack((leading, trailing[1:]))
        base_center = ((front + rear) / 2.0, shape.top_at((front + rear) / 2.0) - 0.01, 0.0)
        fins.add_fan(base_center, rim, self.dark_fin_color, self.dark_fin_color, apex, self.fin_tip_color)
        for front, rear, height, upper in ((-0.265, -0.30, 0.024, True), (-0.275, -0.31, 0.022, False)):
            level_front = shape.top_at(front) if upper else shape.bottom_at(front)
            level_rear = shape.top_at(rear) if upper else shape.bottom_at(rear)
            sign = 1.0 if upper else -1.0
            tip = (rear - 0.012, level_rear + sign * height, 0.0)
            rim = ((front, level_front - sign * 0.004, 0.0), tip, (rear, level_rear - sign * 0.004, 0.0))
            color = self.dark_fin_color if upper else self.fin_belly_color
            fins.add_fan(((front + rear) / 2.0, (level_front + level_rear) / 2.0 - sign * 0.004, 0.0), rim, color, color)

    def add_pectoral_fins(self, fins):
        center, _, half_width = self.shape.girth_at(0.08)
        root_level = center - 0.045
        for side in (1.0, -1.0):
            root_front = (0.13, root_level, side * half_width * 0.8)
            root_rear = (0.02, root_level - 0.01, side * half_width * 0.8)
            tip = (-0.15, root_level - 0.15, side * (half_width + 0.20))
            leading = self.edge(root_front, (0.04, root_level - 0.05, side * (half_width + 0.14)), tip)
            trailing = self.edge(tip, (-0.03, root_level - 0.06, side * (half_width + 0.07)), root_rear)
            rim = numpy.vstack((leading, trailing[1:]))
            root_center = (0.075, root_level - 0.005, side * half_width * 0.8)
            fins.add_fan(root_center, rim, self.fin_top_color, self.fin_belly_color, tip, self.fin_tip_color)

    def add_pelvic_fins(self, fins):
        for side in (1.0, -1.0):
            front, rear = -0.15, -0.20
            level = self.shape.bottom_at(-0.175) + 0.008
            tip = (-0.225, level - 0.045, side * 0.04)
            rim = ((front, level, side * 0.012), tip, (rear, level, side * 0.012))
            fins.add_fan((-0.175, level + 0.004, side * 0.01), rim, self.fin_top_color, self.fin_belly_color)

    def add_caudal_fin(self, fins):
        base_x = self.shape.x_at(1.0)
        center = self.shape.girth_at(base_x)[0]
        peduncle_top = (base_x + 0.012, center + 0.016, 0.0)
        peduncle_bottom = (base_x + 0.012, center - 0.016, 0.0)
        upper_tip = (base_x - 0.14, center + 0.20, 0.0)
        lower_tip = (base_x - 0.11, center - 0.15, 0.0)
        notch = (base_x - 0.065, center + 0.004, 0.0)
        upper_leading = self.edge(peduncle_top, (base_x - 0.05, center + 0.07, 0.0), upper_tip)
        upper_trailing = self.edge(upper_tip, (base_x - 0.085, center + 0.075, 0.0), notch)
        lower_trailing = self.edge(notch, (base_x - 0.085, center - 0.06, 0.0), lower_tip)
        lower_leading = self.edge(lower_tip, (base_x - 0.045, center - 0.055, 0.0), peduncle_bottom)
        base_center = (base_x + 0.005, center, 0.0)
        upper = numpy.vstack((upper_leading, upper_trailing[1:]))
        lower = numpy.vstack((lower_trailing, lower_leading[1:]))
        fins.add_fan(base_center, upper, self.dark_fin_color, self.dark_fin_color, upper_tip, self.fin_tip_color)
        fins.add_fan(base_center, lower, self.dark_fin_color, self.dark_fin_color, lower_tip, self.fin_tip_color)


class Shark:

    def __init__(self, length, model=None):
        self.model = model or SharkModel()
        self.length = length
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.tail_phase = 0.0
        self.reference_length = 4.5
        self.tail_beats_per_second = 0.9 * math.sqrt(self.reference_length / length)
        self.swing = 0.075
        self.wavelength = 1.05
        self.sheen_light = (0.55, 0.55, 0.52, 1.0)
        self.sheen_material = (0.45, 0.45, 0.45, 1.0)
        self.sheen_shininess = 28.0
        self.body_positions = self.model.body_positions.copy()
        self.body_normals = self.model.body_normals.copy()
        self.fin_positions = self.model.fin_positions.copy()
        self.fin_normals = self.model.fin_normals.copy()

    def swim_toward(self, direction):
        dx, dy, dz = direction
        self.yaw = math.atan2(-dz, dx)
        self.pitch = math.atan2(dy, math.hypot(dx, dz))

    def update(self, seconds):
        self.tail_phase = (self.tail_phase + seconds * self.tail_beats_per_second * 2.0 * math.pi) % (2.0 * math.pi)
        self.bend(self.model.body_positions, self.model.body_normals, self.body_positions, self.body_normals)
        self.bend(self.model.fin_positions, self.model.fin_normals, self.fin_positions, self.fin_normals)

    def bend(self, rest_positions, rest_normals, positions, normals):
        from_snout = self.model.shape.snout_x - rest_positions[:, 0]
        envelope = from_snout * from_snout
        wave_number = 2.0 * math.pi / self.wavelength
        wave = wave_number * from_snout - self.tail_phase
        offset = self.swing * envelope * numpy.sin(wave)
        slope_from_snout = self.swing * (2.0 * from_snout * numpy.sin(wave) + envelope * wave_number * numpy.cos(wave))
        positions[:, 2] = rest_positions[:, 2] + offset
        normals[:, 0] = rest_normals[:, 0] + slope_from_snout * rest_normals[:, 2]
        normals[:, 1] = rest_normals[:, 1]
        normals[:, 2] = rest_normals[:, 2]

    def render(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(math.degrees(self.yaw), 0.0, 1.0, 0.0)
        glRotatef(math.degrees(self.pitch), 0.0, 0.0, 1.0)
        glRotatef(math.degrees(self.roll), 1.0, 0.0, 0.0)
        glScalef(self.length, self.length, self.length)
        glPushAttrib(GL_LIGHTING_BIT)
        glLightfv(GL_LIGHT0, GL_SPECULAR, self.sheen_light)
        glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.sheen_material)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.sheen_shininess)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        self.draw_body()
        self.draw_fins()
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()

    def draw_body(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.model.texture)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glColor3f(1.0, 1.0, 1.0)
        glVertexPointer(3, GL_FLOAT, 0, self.body_positions)
        glNormalPointer(GL_FLOAT, 0, self.body_normals)
        glTexCoordPointer(2, GL_FLOAT, 0, self.model.body_texture_points)
        glDrawElements(GL_TRIANGLES, len(self.model.body_indices), GL_UNSIGNED_INT, self.model.body_indices)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

    def draw_fins(self):
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.fin_positions)
        glNormalPointer(GL_FLOAT, 0, self.fin_normals)
        glColorPointer(3, GL_FLOAT, 0, self.model.fin_colors)
        glDrawArrays(GL_TRIANGLES, 0, len(self.fin_positions))
        glDisableClientState(GL_COLOR_ARRAY)
