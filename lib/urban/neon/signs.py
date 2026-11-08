import numpy
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_ARRAY,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_FLOAT,
    GL_LIGHTING,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_COORD_ARRAY,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glColorPointer,
    glDepthMask,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glPopAttrib,
    glPushAttrib,
    glTexCoordPointer,
    glVertexPointer,
)

from lib.urban.neon.textures import SignArt


class FacadeFace:

    def __init__(self, origin, right, up, normal, width, height):
        self.origin = origin
        self.right = right
        self.up = up
        self.normal = normal
        self.width = width
        self.height = height

    @staticmethod
    def of_glass_facade(facade):
        plane = facade.plane
        return FacadeFace(plane.corner, plane.first_edge.normalized(), plane.second_edge.normalized(),
                          plane.normal, plane.first_edge.length(), plane.second_edge.length())

    def point(self, across, height, offset):
        return self.origin + self.right * across + self.up * height + self.normal * offset


class NeonSign:

    def __init__(self, corners, facing, art, flickers, glow_spread, glow_strength):
        self.corners = corners
        self.facing = facing
        self.art = art
        self.flickers = flickers
        self.glow_spread = glow_spread
        self.glow_strength = glow_strength

    def glow_corners(self):
        bottom_left, bottom_right, _, top_left = self.corners
        center = (self.corners[0] + self.corners[2]) * 0.5
        half_across = (bottom_right - bottom_left) * (0.5 * self.glow_spread)
        half_up = (top_left - bottom_left) * (0.5 * self.glow_spread)
        lifted = center + self.facing * 0.15
        return (lifted - half_across - half_up, lifted + half_across - half_up,
                lifted + half_across + half_up, lifted - half_across + half_up)


class SignField:

    def __init__(self, randomness):
        self.randomness = randomness
        self.signs = []
        self.flicker_rate = 0.25
        self.dim_duration = 0.12
        self.dimmed_brightness = 0.25
        self.hum_depth = 0.07
        self.elapsed = 0.0
        self.positions = None

    def add(self, sign):
        self.signs.append(sign)

    def seal(self, glow_region):
        count = len(self.signs)
        self.positions = numpy.array([tuple(corner) for sign in self.signs for corner in sign.corners],
                                     dtype=numpy.float32).reshape(-1, 3)
        self.texture_corners = numpy.array([corner for sign in self.signs for corner in sign.art.region.corners()],
                                           dtype=numpy.float32).reshape(-1, 2)
        self.glow_positions = numpy.array([tuple(corner) for sign in self.signs for corner in sign.glow_corners()],
                                          dtype=numpy.float32).reshape(-1, 3)
        self.glow_texture_corners = numpy.tile(numpy.array(glow_region.corners(), dtype=numpy.float32), (count, 1))
        self.glow_tints = numpy.array([[channel / 255.0 * sign.glow_strength for channel in sign.art.glow_color]
                                       for sign in self.signs], dtype=numpy.float32).reshape(-1, 3)
        self.flickering = numpy.array([sign.flickers for sign in self.signs], dtype=bool)
        self.dim_left = numpy.zeros(count, dtype=numpy.float32)
        self.hum_phase = numpy.array([self.randomness.uniform(0.0, 6.28) for _ in self.signs], dtype=numpy.float32)
        self.hum_speed = numpy.array([self.randomness.uniform(3.0, 9.0) for _ in self.signs], dtype=numpy.float32)
        self.colors = numpy.ones((4 * count, 4), dtype=numpy.float32)
        self.glow_colors = numpy.ones((4 * count, 4), dtype=numpy.float32)
        self.update(0.0)

    def update(self, seconds):
        self.elapsed += seconds
        count = len(self.signs)
        self.dim_left = numpy.maximum(self.dim_left - seconds, 0.0)
        starts = self.flickering & (numpy.random.random(count) < self.flicker_rate * seconds)
        self.dim_left[starts] = self.dim_duration
        hum = 1.0 - self.hum_depth * (0.5 + 0.5 * numpy.sin(self.hum_phase + self.elapsed * self.hum_speed))
        brightness = numpy.where(self.dim_left > 0.0, self.dimmed_brightness, hum).astype(numpy.float32)
        per_corner = numpy.repeat(brightness, 4)
        self.colors[:, 0] = per_corner
        self.colors[:, 1] = per_corner
        self.colors[:, 2] = per_corner
        self.glow_colors[:, :3] = numpy.repeat(self.glow_tints * brightness[:, None], 4, axis=0)

    def draw_signs(self, atlas_texture):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        atlas_texture.bind()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._draw_arrays(self.positions, self.texture_corners, self.colors)
        glPopAttrib()

    def draw_glows(self, atlas_texture):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        atlas_texture.bind()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        self._draw_arrays(self.glow_positions, self.glow_texture_corners, self.glow_colors)
        glPopAttrib()

    def _draw_arrays(self, positions, texture_corners, colors):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glTexCoordPointer(2, GL_FLOAT, 0, texture_corners)
        glColorPointer(4, GL_FLOAT, 0, colors)
        glDrawArrays(GL_QUADS, 0, len(positions))
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)


class SignArtLibrary:

    def __init__(self, painter, sprite_painter, atlas):
        self.kinds = {}
        self.pool_sizes = {"vertical": 18, "horizontal": 16, "banner": 12, "billboard": 14,
                           "screen": 10, "storefront": 10}
        painters = {"vertical": painter.vertical_glyphs, "horizontal": painter.horizontal_glyphs,
                    "banner": painter.tall_banner, "billboard": painter.billboard,
                    "screen": painter.screen, "storefront": painter.storefront}
        for kind, paint in painters.items():
            self.kinds[kind] = [self._store(atlas, *paint()) for _ in range(self.pool_sizes[kind])]
        self.glow_region = atlas.add(sprite_painter.glow(64))
        self.walker_regions = [atlas.add(sprite_painter.walker(variant)) for variant in range(4)]

    def _store(self, atlas, surface, glow_color):
        width, height = surface.get_size()
        return SignArt(atlas.add(surface), glow_color, width / height)

    def pick(self, kind, randomness):
        return randomness.choice(self.kinds[kind])


class SignDresser:

    def __init__(self, library, randomness):
        self.library = library
        self.randomness = randomness
        self.wall_offset = 0.25
        self.spacing = 0.35
        self.storefront_height = 2.6
        self.storefront_base = 0.5
        self.lowest_sign = 5.8
        self.square_meters_per_sign = 45.0
        self.most_signs = 22
        self.flicker_chance = 0.18
        self.blade_reach = 2.2
        self.kind_weights = (("vertical", 0.28), ("horizontal", 0.22), ("banner", 0.16),
                             ("billboard", 0.18), ("screen", 0.16))
        self.size_ranges = {"vertical": (1.3, 2.4), "horizontal": (4.0, 9.0), "banner": (2.4, 4.4),
                            "billboard": (7.0, 15.0), "screen": (4.0, 9.0)}

    def dress(self, face, field, density):
        if face.width > 3.0:
            self._storefront(face, field)
        taken = []
        wanted = min(self.most_signs, int(density * face.width * face.height / self.square_meters_per_sign))
        attempts = wanted * 6
        while wanted > 0 and attempts > 0:
            attempts -= 1
            if self._try_flat_sign(face, field, taken):
                wanted -= 1
        if face.width > 6.0:
            for _ in range(self.randomness.randint(1, 2)):
                self._blade(face, field)

    def _storefront(self, face, field):
        art = self.library.pick("storefront", self.randomness)
        left = 0.4
        right = face.width - 0.4
        corners = self._flat_corners(face, left, self.storefront_base, right - left, self.storefront_height)
        field.add(NeonSign(corners, face.normal, art, False, 1.6, 0.55))

    def _try_flat_sign(self, face, field, taken):
        kind = self._weighted_kind()
        art = self.library.pick(kind, self.randomness)
        smallest, largest = self.size_ranges[kind]
        width = min(self.randomness.uniform(smallest, largest), face.width - 1.0)
        height = width / art.aspect
        if width < 1.0 or height > face.height - self.lowest_sign - 1.0:
            return False
        across = self.randomness.uniform(0.5, face.width - width - 0.5)
        rise = self.randomness.uniform(self.lowest_sign, face.height - height - 0.5)
        rectangle = (across - self.spacing, rise - self.spacing, across + width + self.spacing, rise + height + self.spacing)
        if any(self._overlaps(rectangle, other) for other in taken):
            return False
        taken.append(rectangle)
        flickers = self.randomness.random() < self.flicker_chance
        glow_spread = 1.5 if kind == "billboard" else 2.0
        field.add(NeonSign(self._flat_corners(face, across, rise, width, height), face.normal, art,
                           flickers, glow_spread, 0.42))
        return True

    def _blade(self, face, field):
        art = self.library.pick("vertical", self.randomness)
        height = self.randomness.uniform(6.0, 11.0)
        if face.height < height + self.lowest_sign + 2.0:
            return
        across = self.randomness.choice((0.6, face.width - 0.6))
        rise = self.randomness.uniform(self.lowest_sign, face.height - height - 1.0)
        base = face.point(across, rise, self.wall_offset)
        tip = base + face.normal * self.blade_reach
        lift = face.up * height
        corners = (base, tip, tip + lift, base + lift)
        field.add(NeonSign(corners, face.right, art, self.randomness.random() < self.flicker_chance, 2.2, 0.5))

    def _flat_corners(self, face, across, rise, width, height):
        return (face.point(across, rise, self.wall_offset),
                face.point(across + width, rise, self.wall_offset),
                face.point(across + width, rise + height, self.wall_offset),
                face.point(across, rise + height, self.wall_offset))

    def _weighted_kind(self):
        roll = self.randomness.random() * sum(weight for _, weight in self.kind_weights)
        for kind, weight in self.kind_weights:
            roll -= weight
            if roll <= 0.0:
                return kind
        return self.kind_weights[-1][0]

    @staticmethod
    def _overlaps(first, second):
        return first[0] < second[2] and second[0] < first[2] and first[1] < second[3] and second[1] < first[3]


class GlowSprites:

    def __init__(self, region):
        self.region = region
        self.texture_corners = numpy.array(region.corners(), dtype=numpy.float32)
        self.centers = numpy.zeros((0, 3), dtype=numpy.float32)
        self.sizes = numpy.zeros(0, dtype=numpy.float32)
        self.tints = numpy.zeros((0, 4), dtype=numpy.float32)

    def set(self, centers, sizes, tints):
        self.centers = numpy.asarray(centers, dtype=numpy.float32).reshape(-1, 3)
        self.sizes = numpy.asarray(sizes, dtype=numpy.float32).reshape(-1)
        self.tints = numpy.asarray(tints, dtype=numpy.float32).reshape(-1, 4)

    def draw(self, atlas_texture, right, up):
        count = len(self.centers)
        if count == 0:
            return
        right_step = numpy.array(tuple(right), dtype=numpy.float32)
        up_step = numpy.array(tuple(up), dtype=numpy.float32)
        offsets = numpy.array([-right_step - up_step, right_step - up_step, right_step + up_step, up_step - right_step])
        positions = (self.centers[:, None, :] + offsets[None, :, :] * self.sizes[:, None, None]).reshape(-1, 3)
        texture_corners = numpy.tile(self.texture_corners, (count, 1))
        colors = numpy.repeat(self.tints, 4, axis=0)
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        atlas_texture.bind()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions.astype(numpy.float32))
        glTexCoordPointer(2, GL_FLOAT, 0, texture_corners)
        glColorPointer(4, GL_FLOAT, 0, colors)
        glDrawArrays(GL_QUADS, 0, len(positions))
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
