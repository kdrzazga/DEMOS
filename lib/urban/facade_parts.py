import math


class WindowStyle:
    def __init__(self, frame_color, glass_color, sash_color, sill_color, hood_color, frieze_color,
                 surround=0.2, depth=0.1):
        self.frame_color = frame_color
        self.glass_color = glass_color
        self.sash_color = sash_color
        self.sill_color = sill_color
        self.hood_color = hood_color
        self.frieze_color = frieze_color
        self.surround = surround
        self.depth = depth


class RectWindow:
    def __init__(self, style, width, height, transoms=(0.68, 0.34), hood=False):
        self.style = style
        self.width = width
        self.height = height
        self.transoms = transoms
        self.hood = hood

    def draw(self, shapes, center_x, bottom):
        style = self.style
        half = self.width / 2.0
        top = bottom + self.height
        rim = style.surround
        shapes.box(center_x - half, bottom, 0.0, center_x + half, top, 0.02, style.glass_color)
        shapes.box(center_x - half - rim, bottom, 0.0, center_x - half, top, style.depth, style.frame_color)
        shapes.box(center_x + half, bottom, 0.0, center_x + half + rim, top, style.depth, style.frame_color)
        shapes.box(center_x - half - rim, top, 0.0, center_x + half + rim, top + rim, style.depth, style.frame_color)
        shapes.box(center_x - 0.04, bottom, 0.0, center_x + 0.04, top, 0.05, style.sash_color)
        for fraction in self.transoms:
            level = bottom + self.height * fraction
            shapes.box(center_x - half, level - 0.04, 0.0, center_x + half, level + 0.04, 0.05, style.sash_color)
        shapes.box(center_x - half - rim - 0.1, bottom - 0.14, 0.0, center_x + half + rim + 0.1, bottom, 0.2,
                   style.sill_color)
        if self.hood:
            self._draw_hood(shapes, center_x, top + rim, half + rim)

    def _draw_hood(self, shapes, center_x, bottom, half):
        style = self.style
        shapes.box(center_x - half, bottom, 0.0, center_x + half, bottom + 0.32, 0.08, style.frieze_color)
        shapes.box(center_x - half - 0.15, bottom + 0.32, 0.0, center_x + half + 0.15, bottom + 0.46, 0.3,
                   style.hood_color)
        shapes.box(center_x - half - 0.08, bottom + 0.46, 0.0, center_x + half + 0.08, bottom + 0.54, 0.22,
                   style.hood_color)


class ArchedWindow:
    def __init__(self, style, width, height, segments=16):
        self.style = style
        self.radius = width / 2.0
        self.height = height
        self.segments = segments

    def draw(self, shapes, center_x, bottom):
        style = self.style
        radius = self.radius
        rim = style.surround
        spring = bottom + self.height - radius
        angles = [math.pi * index / self.segments for index in range(self.segments + 1)]
        shapes.box(center_x - radius, bottom, 0.0, center_x + radius, spring, 0.02, style.glass_color)
        glass = [(center_x + radius * math.cos(angle), spring + radius * math.sin(angle), 0.02) for angle in angles]
        shapes.fan((center_x, spring, 0.02), glass, (0.0, 0.0, 1.0), style.glass_color)
        shapes.box(center_x - radius - rim, bottom, 0.0, center_x - radius, spring, style.depth, style.frame_color)
        shapes.box(center_x + radius, bottom, 0.0, center_x + radius + rim, spring, style.depth, style.frame_color)
        self._draw_arch_band(shapes, center_x, spring, angles)
        shapes.box(center_x - 0.16, spring + radius - 0.05, 0.0, center_x + 0.16, spring + radius + rim + 0.14,
                   style.depth + 0.04, style.frieze_color)
        shapes.box(center_x - 0.04, bottom, 0.0, center_x + 0.04, spring + radius, 0.05, style.sash_color)
        for level in (spring, (bottom + spring) / 2.0):
            shapes.box(center_x - radius, level - 0.04, 0.0, center_x + radius, level + 0.04, 0.05, style.sash_color)
        shapes.box(center_x - radius - rim - 0.1, bottom - 0.14, 0.0, center_x + radius + rim + 0.1, bottom, 0.2,
                   style.sill_color)

    def _draw_arch_band(self, shapes, center_x, spring, angles):
        style = self.style
        inner = self.radius
        outer = self.radius + style.surround
        face = [((center_x + inner * math.cos(angle), spring + inner * math.sin(angle), style.depth),
                 (center_x + outer * math.cos(angle), spring + outer * math.sin(angle), style.depth))
                for angle in angles]
        shapes.strip(face, [(0.0, 0.0, 1.0)] * len(face), style.frame_color)
        rim = [((center_x + outer * math.cos(angle), spring + outer * math.sin(angle), 0.0),
                (center_x + outer * math.cos(angle), spring + outer * math.sin(angle), style.depth))
               for angle in angles]
        shapes.strip(rim, [(math.cos(angle), math.sin(angle), 0.0) for angle in angles], style.frame_color)


class Rustication:
    def __init__(self, stone_color, joint_color, course_height=0.55, depth=0.2, inset=0.2):
        self.stone_color = stone_color
        self.joint_color = joint_color
        self.course_height = course_height
        self.depth = depth
        self.inset = inset

    def draw(self, shapes, left, right, bottom, top):
        shapes.box(left, bottom, 0.0, right, top, self.depth * 0.5, self.joint_color)
        level = bottom
        course = 0
        while level < top - 0.05:
            upper = min(top, level + self.course_height)
            shift = self.inset if course % 2 else 0.0
            shapes.box(left + shift, level + 0.035, 0.0, right - self.inset + shift, upper - 0.035, self.depth,
                       self.stone_color)
            level = upper
            course += 1


class DentilCourse:
    def __init__(self, tooth_color, shadow_color, tooth_width=0.16, spacing=0.34, height=0.22, depth=0.16):
        self.tooth_color = tooth_color
        self.shadow_color = shadow_color
        self.tooth_width = tooth_width
        self.spacing = spacing
        self.height = height
        self.depth = depth

    def draw(self, shapes, left, right, bottom):
        top = bottom + self.height
        shapes.box(left, bottom, 0.0, right, top, self.depth * 0.4, self.shadow_color)
        center = left + self.spacing / 2.0
        half = self.tooth_width / 2.0
        while center < right:
            shapes.box(center - half, bottom, 0.0, center + half, top, self.depth, self.tooth_color)
            center += self.spacing


class Cornice:
    def __init__(self, layers, bracket_color, bracket_spacing=1.1):
        self.layers = layers
        self.bracket_color = bracket_color
        self.bracket_spacing = bracket_spacing

    def height(self):
        return sum(thickness for thickness, _, _ in self.layers)

    def draw(self, shapes, left, right, bottom):
        level = bottom
        for thickness, projection, color in self.layers:
            shapes.box(left - projection, level, 0.0, right + projection, level + thickness, projection, color)
            level += thickness
        crown_thickness, crown_projection, _ = self.layers[-1]
        bracket_bottom = bottom + self.layers[0][0]
        bracket_top = level - crown_thickness
        center = left + self.bracket_spacing / 2.0
        while center < right:
            shapes.box(center - 0.1, bracket_bottom, 0.0, center + 0.1, bracket_top, crown_projection * 0.85,
                       self.bracket_color)
            center += self.bracket_spacing


class ArcadeWall:
    def __init__(self, color, soffit_color, impost_color, thickness=0.6, segments=14):
        self.color = color
        self.soffit_color = soffit_color
        self.impost_color = impost_color
        self.thickness = thickness
        self.segments = segments

    def draw(self, shapes, length, top, openings):
        cursor = 0.0
        for center, half, spring in sorted(openings):
            shapes.box(cursor, 0.0, -self.thickness, center - half, top, 0.0, self.color)
            self._draw_spandrel(shapes, center, half, spring, top)
            self._draw_imposts(shapes, center, half, spring)
            cursor = center + half
        shapes.box(cursor, 0.0, -self.thickness, length, top, 0.0, self.color)

    def _draw_spandrel(self, shapes, center, half, spring, top):
        depth = -self.thickness
        angles = [math.pi - math.pi * index / self.segments for index in range(self.segments + 1)]
        arc = [(center + half * math.cos(angle), spring + half * math.sin(angle)) for angle in angles]
        shapes.strip([((x, y, 0.0), (x, top, 0.0)) for x, y in arc], [(0.0, 0.0, 1.0)] * len(arc), self.color)
        shapes.strip([((x, y, depth), (x, top, depth)) for x, y in arc], [(0.0, 0.0, -1.0)] * len(arc), self.color)
        shapes.strip([((x, y, 0.0), (x, y, depth)) for x, y in arc],
                     [(-math.cos(angle), -math.sin(angle), 0.0) for angle in angles], self.soffit_color)

    def _draw_imposts(self, shapes, center, half, spring):
        for edge, direction in ((center - half, 1.0), (center + half, -1.0)):
            shapes.box(edge - 0.12 * direction, spring - 0.2, -self.thickness - 0.05, edge + 0.1 * direction, spring,
                       0.06, self.impost_color)
