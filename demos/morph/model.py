"""Triangle meshes of the stronghold that morph between the flat drawing and 3D."""
import numpy as np
from PIL import Image, ImageDraw


class Mesh:
    """Vertices remember their place in the flat drawing and their full depth;
    ``morph`` (0 = flat drawing, 1 = full 3D) scales the depth in between."""

    def __init__(self, pixel, depth, depth_fix, stretch, normal, fixed_normal, uv_pixel, highlight, triangles,
                 image_size, pixels_per_unit):
        width, height = image_size
        self.positions = np.zeros((len(depth), 3), np.float32)
        self.world_x = ((pixel[:, 0] - width / 2) / pixels_per_unit).astype(np.float32)
        self.positions[:, 0] = self.world_x
        self.positions[:, 1] = (height / 2 - pixel[:, 1]) / pixels_per_unit
        self.world_depth = (depth / pixels_per_unit).astype(np.float32)
        self.world_depth_fix = (depth_fix / pixels_per_unit).astype(np.float32)
        self.world_stretch = (stretch / pixels_per_unit).astype(np.float32)
        self.normal = normal.astype(np.float32)
        self.fixed_normal = fixed_normal.astype(np.float32)
        self.uv = (uv_pixel / np.array([width, height])).astype(np.float32)
        self.highlight = highlight.astype(np.float32)
        self.triangles = triangles.astype(np.uint32).ravel()

    def positions_at(self, morph, fix=0.0):
        """fix (0..1) blends in each piece's depth_fix and sideways stretch; both
        vanish again as morph returns to the flat drawing."""
        self.positions[:, 0] = self.world_x + self.world_stretch * (fix * morph)
        self.positions[:, 2] = (self.world_depth + self.world_depth_fix * fix) * morph
        return self.positions

    def shading_at(self, morph, light_direction, fix=0.0):
        """1.0 everywhere while flat (looks like paper), lambert lighting once 3D;
        fix turns the normals of surfaces the 'small fix' bends."""
        normal = (self.normal * (1.0 - fix) + self.fixed_normal * fix) * morph
        normal[:, 2] += 1.0 - morph
        length = np.maximum(np.linalg.norm(normal, axis=1), 1e-6)
        lambert = np.clip((normal @ light_direction) / length, 0.0, 1.0)
        return 1.0 - morph * (1.0 - (0.45 + 0.55 * lambert))


class RockMesh:
    """Opaque relief over the rocky hill: a regular pixel grid whose depth is the
    bent backdrop (scaled by morph) plus the swelling (scaled by lift)."""

    def __init__(self, pixel_x, pixel_y, base_depth, swell, swell_depth, inside, image_size, pixels_per_unit):
        width, height = image_size
        rows, columns = swell.shape
        grid_x, grid_y = np.meshgrid(pixel_x, pixel_y)
        self.step_x = (pixel_x[1] - pixel_x[0]) / pixels_per_unit
        self.step_y = (pixel_y[1] - pixel_y[0]) / pixels_per_unit
        self.positions = np.zeros((rows * columns, 3), np.float32)
        self.positions[:, 0] = (grid_x.ravel() - width / 2) / pixels_per_unit
        self.positions[:, 1] = (height / 2 - grid_y.ravel()) / pixels_per_unit
        self.base_depth = np.broadcast_to(base_depth / pixels_per_unit, swell.shape).astype(np.float32)
        self.swell_depth = (swell * swell_depth / pixels_per_unit).astype(np.float32)
        self.swell = swell.ravel().astype(np.float32)
        self.uv = np.column_stack((grid_x.ravel() / width, grid_y.ravel() / height)).astype(np.float32)
        self.depth = np.zeros(swell.shape, np.float32)

        index = np.arange(rows * columns).reshape(rows, columns)
        top_left, top_right = index[:-1, :-1], index[:-1, 1:]
        bottom_left, bottom_right = index[1:, :-1], index[1:, 1:]
        touches_rock = inside[:-1, :-1] | inside[:-1, 1:] | inside[1:, :-1] | inside[1:, 1:]
        quads = np.stack((top_left, bottom_left, top_right, top_right, bottom_left, bottom_right), axis=-1)
        self.triangles = quads[touches_rock].astype(np.uint32).ravel()

    def positions_at(self, morph, lift):
        self.depth = self.base_depth * morph + self.swell_depth * lift
        self.positions[:, 2] = self.depth.ravel()
        return self.positions

    def shading_at(self, morph, light_direction):
        """Lighting from the current depth field; call after positions_at."""
        depth_down_rows, depth_across = np.gradient(self.depth, self.step_y, self.step_x)
        # surface z = f(x, y) has normal (-df/dx, -df/dy, 1); rows run towards -y
        normal = np.stack((-depth_across, depth_down_rows, np.ones_like(depth_across)), axis=-1).reshape(-1, 3)
        lambert = np.clip((normal @ light_direction) / np.linalg.norm(normal, axis=1), 0.0, 1.0)
        return 1.0 - morph * (1.0 - (0.45 + 0.55 * lambert))


class MeshBuilder:
    """Collects quad grids (2D arrays of vertices) into one triangle mesh."""

    def __init__(self):
        self.grids = []
        self.vertex_count = 0
        self.depth_fix = 0.0  # given to every grid added until changed

    def add_grid(self, pixel_x, pixel_y, depth, normal, uv_x, uv_y, highlight, stretch=0.0, depth_shift=0.0,
                 fixed_normal=None):
        """What the 'small fix' does to each vertex: stretch slides it right and
        depth_shift moves it forward (pixels, on top of the builder's depth_fix);
        fixed_normal is its normal afterwards (default: unchanged)."""
        shape = np.broadcast_shapes(np.shape(pixel_x), np.shape(pixel_y), np.shape(depth))
        rows, columns = shape
        index = np.arange(rows * columns).reshape(shape) + self.vertex_count
        top_left, top_right = index[:-1, :-1], index[:-1, 1:]
        bottom_left, bottom_right = index[1:, :-1], index[1:, 1:]
        triangles = np.stack((top_left, bottom_left, top_right, top_right, bottom_left, bottom_right), axis=-1)

        def flat(values, width=None):
            target = shape if width is None else shape + (width,)
            return np.broadcast_to(np.asarray(values, np.float64), target).reshape(rows * columns, -1)

        self.grids.append((
            np.hstack((flat(pixel_x), flat(pixel_y))),
            flat(depth).ravel(),
            self.depth_fix + flat(depth_shift).ravel(),
            flat(stretch).ravel(),
            flat(normal, 3),
            flat(normal if fixed_normal is None else fixed_normal, 3),
            np.hstack((flat(uv_x), flat(uv_y))),
            flat(highlight, 3),
            triangles.reshape(-1, 3),
        ))
        self.vertex_count += rows * columns

    def build(self, image_size, pixels_per_unit):
        pixel, depth, depth_fix, stretch, normal, fixed_normal, uv, highlight, triangles = (
            np.concatenate(part) for part in zip(*self.grids))
        return Mesh(pixel, depth, depth_fix, stretch, normal, fixed_normal, uv, highlight, triangles, image_size,
                    pixels_per_unit)


class StrongholdModel:
    """Solid towers and walls, the rocky hill as an opaque relief, and a bent
    'stage flat' sheet that carries the remaining ink with both cut out."""

    def __init__(self, drawing, pieces, rock_zone, pixels_per_unit=500.0, paper_pixel=(20, 20), mask_growth=6,
                 backdrop_profile=((0, -450), (650, -350), (800, 0), (900, 200), (1282, 450)),
                 sheet_columns=80, sheet_rows=50, swell_depth=90.0, plateau_pixels=80, rock_grid_step=6):
        self.drawing = drawing
        self.pieces = pieces
        self.pixels_per_unit = pixels_per_unit
        profile_y, profile_depth = zip(*backdrop_profile)

        solids = MeshBuilder()
        for piece in pieces:
            piece.detect(drawing)
            solids.depth_fix = piece.depth_fix
            piece.build(solids, paper_pixel)
        self.solids = solids.build(drawing.size, pixels_per_unit)
        footprints = [piece.footprint() for piece in pieces]

        self.swell_map, self.swell_downscale = drawing.swelling(rock_zone, footprints, mask_growth, plateau_pixels)
        self.rocks = self._build_rocks(rock_zone, footprints, profile_y, profile_depth, swell_depth, rock_grid_step)

        self.backdrop_ink = drawing.ink_outside(footprints + [rock_zone], mask_growth)
        sheet = MeshBuilder()
        sheet_x = np.linspace(0.0, drawing.width, sheet_columns + 1)[None, :]
        sheet_y = np.linspace(0.0, drawing.height, sheet_rows + 1)[:, None]
        sheet_depth = np.interp(sheet_y, profile_y, profile_depth)
        sheet.add_grid(sheet_x, sheet_y, sheet_depth, (0.0, 0.0, 1.0), sheet_x, sheet_y, (0.0, 0.0, 0.0))
        self.sheet = sheet.build(drawing.size, pixels_per_unit)

    def _build_rocks(self, rock_zone, footprints, profile_y, profile_depth, swell_depth, grid_step):
        drawing = self.drawing
        zone_top = float(rock_zone[:, 1].min())
        pixel_x = np.linspace(0.0, drawing.width, int(np.ceil(drawing.width / grid_step)) + 1)
        pixel_y = np.linspace(zone_top, drawing.height, int(np.ceil((drawing.height - zone_top) / grid_step)) + 1)

        rock_area = Image.new("L", drawing.size, 0)
        draw = ImageDraw.Draw(rock_area)
        draw.polygon([(float(x), float(y)) for x, y in rock_zone], fill=255)
        for footprint in footprints:
            draw.polygon([(float(x), float(y)) for x, y in footprint], fill=0)
        column = np.minimum(pixel_x.astype(int), drawing.width - 1)[None, :]
        row = np.minimum(pixel_y.astype(int), drawing.height - 1)[:, None]
        inside = np.asarray(rock_area)[row, column] > 0

        small_rows, small_columns = self.swell_map.shape
        swell = self.swell_map[np.minimum(row // self.swell_downscale, small_rows - 1),
                               np.minimum(column // self.swell_downscale, small_columns - 1)]
        base_depth = np.interp(pixel_y, profile_y, profile_depth)[:, None]
        return RockMesh(pixel_x, pixel_y, base_depth, swell, swell_depth, inside, drawing.size,
                        self.pixels_per_unit)

    @property
    def world_size(self):
        return self.drawing.width / self.pixels_per_unit, self.drawing.height / self.pixels_per_unit

    def to_world(self, pixel_x, pixel_y):
        return ((pixel_x - self.drawing.width / 2) / self.pixels_per_unit,
                (self.drawing.height / 2 - pixel_y) / self.pixels_per_unit)
