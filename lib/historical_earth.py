import os

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluSphere

from lib.earth import Earth


# (name, latitude, longitude): coastline extremes and cities the historical maps are pinned to.
PLACES = (
    ("Cape Agulhas", -34.83, 20.00),
    ("Cape Horn", -55.98, -67.27),
    ("South East Cape", -43.64, 146.83),
    ("Kanyakumari", 8.08, 77.54),
    ("Dondra Head", 5.92, 80.59),
    ("Ponta do Seixas", -7.15, -34.79),
    ("Cap-Vert", 14.73, -17.53),
    ("Ras Hafun", 10.44, 51.41),
    ("Cabo da Roca", 38.78, -9.50),
    ("Cape Byron", -28.64, 153.64),
    ("Steep Point", -26.15, 113.16),
    ("North Cape", 71.18, 25.78),
    ("Cape Morris Jesup", 83.66, -33.40),
    ("Antarctic Peninsula", -63.20, -57.00),
    ("Cape Prince of Wales", 65.60, -168.10),
    ("Cape Dezhnev", 66.08, -169.66),
    ("Florida Keys", 25.12, -81.08),
    ("Cabo San Lucas", 22.88, -109.90),
    ("Punta Parinas", -4.68, -81.33),
    ("Cape Spear", 47.52, -52.62),
    ("Point Barrow", 71.39, -156.50),
    ("Cape Lopatka", 50.87, 156.67),
    ("Ca Mau", 8.60, 104.70),
    ("Cape Sainte Marie", -25.60, 45.15),
    ("Cap d'Ambre", -11.95, 49.26),
    ("Stewart Island", -47.30, 167.50),
    ("North Cape NZ", -34.40, 173.00),
    ("Cape Mendocino", 40.44, -124.40),
    ("Cape Farewell", 59.77, -43.90),
    ("Dunmore Head", 52.10, -10.48),
    ("Cape Chidley", 60.40, -64.40),
    ("Cape Palmas", 4.37, -7.73),
    ("Lodz", 51.76, 19.46),
    ("Auschwitz", 50.03, 19.20),
    ("Bergen-Belsen", 52.76, 9.91),
    ("New York", 40.71, -74.01),
    ("Toronto", 43.65, -79.38),
    ("Monte Sereno", 37.24, -121.99),
)

# Where each place sits on world1936.png (4496x2572). The map is hand drawn, not a true projection,
# so it is warped onto the globe through these points.
WORLD1936_PIXELS = {
    "Cape Agulhas": (2095, 1794), "Cape Horn": (1089, 2105), "South East Cape": (3784, 1888),
    "Kanyakumari": (2890, 1126), "Dondra Head": (2933, 1165), "Ponta do Seixas": (1356, 1360),
    "Cap-Vert": (1593, 1024), "Ras Hafun": (2532, 1069), "Cabo da Roca": (1718, 647),
    "Cape Byron": (3901, 1619), "Steep Point": (3411, 1618), "North Cape": (2120, 181),
    "Cape Morris Jesup": (1620, 39), "Antarctic Peninsula": (1282, 2137), "Cape Prince of Wales": (19, 392),
    "Cape Dezhnev": (3828, 268), "Florida Keys": (755, 858), "Cabo San Lucas": (359, 882),
    "Punta Parinas": (713, 1324), "Cape Spear": (1209, 486), "Point Barrow": (349, 182),
    "Cape Lopatka": (3704, 459), "Ca Mau": (3271, 1116), "Cape Sainte Marie": (2438, 1653),
    "Cap d'Ambre": (2503, 1441), "Stewart Island": (4013, 2041), "North Cape NZ": (4193, 1851),
    "Cape Mendocino": (265, 648), "Cape Farewell": (1376, 326), "Dunmore Head": (1728, 443),
    "Cape Chidley": (1148, 338), "Cape Palmas": (1699, 1169),
    "Lodz": (2080, 448), "Auschwitz": (2072, 476), "Bergen-Belsen": (1969, 434),
    "New York": (907, 617), "Toronto": (863, 573), "Monte Sereno": (277, 692),
}

# Where each place sits on world1942.png (1357x628). This map draws no Antarctica.
WORLD1942_PIXELS = {
    "Cape Agulhas": (640, 518), "Cape Horn": (323, 611), "South East Cape": (1111, 560),
    "Kanyakumari": (877, 324), "Dondra Head": (890, 335), "Ponta do Seixas": (411, 394),
    "Cap-Vert": (486, 294), "Ras Hafun": (776, 304), "Cabo da Roca": (524, 185),
    "Cape Byron": (1173, 486), "Steep Point": (1017, 489), "North Cape": (638, 53),
    "Cape Morris Jesup": (476, 12), "Cape Prince of Wales": (8, 112), "Cape Dezhnev": (1159, 75),
    "Florida Keys": (230, 248), "Cabo San Lucas": (109, 256), "Punta Parinas": (219, 369),
    "Cape Spear": (366, 146), "Point Barrow": (48, 70), "Cape Lopatka": (1121, 131),
    "Ca Mau": (981, 322), "Cape Sainte Marie": (741, 478), "Cap d'Ambre": (772, 415),
    "Stewart Island": (1181, 569), "North Cape NZ": (1237, 522), "Cape Mendocino": (82, 186),
    "Cape Farewell": (415, 93), "Dunmore Head": (527, 128), "Cape Chidley": (344, 97),
    "Cape Palmas": (524, 342),
    "Lodz": (625, 130), "Auschwitz": (627, 135), "Bergen-Belsen": (593, 127),
    "New York": (272, 180), "Toronto": (259, 169), "Monte Sereno": (87, 199),
}

# Where each place sits on modern.png (1300x628). Like the 1942 map, it draws no Antarctica.
MODERN_PIXELS = {
    "Cape Agulhas": (639, 535), "Cape Horn": (318, 627), "South East Cape": (1111, 578),
    "Kanyakumari": (877, 329), "Dondra Head": (891, 343), "Ponta do Seixas": (407, 403),
    "Cap-Vert": (480, 300), "Ras Hafun": (767, 314), "Cabo da Roca": (518, 185),
    "Cape Byron": (1178, 490), "Steep Point": (1015, 494), "North Cape": (635, 43),
    "Cape Morris Jesup": (463, 1), "Cape Prince of Wales": (0, 107), "Cape Dezhnev": (1163, 69),
    "Florida Keys": (224, 251), "Cabo San Lucas": (102, 258), "Punta Parinas": (212, 376),
    "Cape Spear": (362, 136), "Point Barrow": (45, 61), "Cape Lopatka": (1123, 128),
    "Ca Mau": (992, 330), "Cape Sainte Marie": (742, 492), "Cap d'Ambre": (758, 428),
    "Stewart Island": (1186, 592), "North Cape NZ": (1240, 535), "Cape Mendocino": (74, 184),
    "Cape Farewell": (412, 88), "Dunmore Head": (521, 123), "Cape Chidley": (342, 88),
    "Cape Palmas": (519, 350),
    "Lodz": (630, 126), "Auschwitz": (629, 133), "Bergen-Belsen": (594, 122),
    "New York": (270, 177), "Toronto": (255, 164), "Monte Sereno": (78, 197),
}

# year: map file in lib/resources, its pinned pixels, texture width on the globe, and how to treat the far south.
HISTORICAL_MAPS = {
    1936: {"file": "world1936.png", "pixels": WORLD1936_PIXELS, "texture_width": 4096,
           "ice_below_map": True, "polar_ice_latitude": -72.0},
    1942: {"file": "world1942.png", "pixels": WORLD1942_PIXELS, "texture_width": 2048,
           "ice_below_map": False, "polar_ice_latitude": -68.0},
    "modern": {"file": "modern.png", "pixels": MODERN_PIXELS, "texture_width": 2048,
               "ice_below_map": False, "polar_ice_latitude": -68.0},
}


class ThinPlateWarp:
    """Smooth mapping from (longitude, latitude) in degrees to map pixels, exact at the control points."""

    def __init__(self, geo_points, map_points, smoothing=0.0, degrees_per_unit=100.0):
        self.degrees_per_unit = degrees_per_unit
        self.centers = np.asarray(geo_points, dtype=np.float64) / degrees_per_unit
        count = len(self.centers)
        affine_terms = np.hstack((np.ones((count, 1)), self.centers))
        system = np.zeros((count + 3, count + 3))
        system[:count, :count] = self._kernel(self.centers) + smoothing * np.eye(count)
        system[:count, count:] = affine_terms
        system[count:, :count] = affine_terms.T
        targets = np.zeros((count + 3, 2))
        targets[:count] = np.asarray(map_points, dtype=np.float64)
        solution = np.linalg.solve(system, targets)
        self.weights = solution[:count]
        self.affine = solution[count:]

    def _kernel(self, points):
        squared_distance = ((points[:, None, :] - self.centers[None, :, :]) ** 2).sum(axis=2)
        return 0.5 * squared_distance * np.log(np.maximum(squared_distance, 1e-12))

    def __call__(self, geo_points):
        points = np.asarray(geo_points, dtype=np.float64) / self.degrees_per_unit
        return self.affine[0] + points @ self.affine[1:] + self._kernel(points) @ self.weights


class HistoricalMap:
    """Reprojects a hand-drawn world map into an equirectangular texture (north up, longitude -180 at left).

    landmarks are (name, latitude, longitude, map x, map y); ice_below_map says the map's bottom edge
    cuts through Antarctica, so everything south of it is ice rather than sea.
    """

    def __init__(self, map_path, landmarks, seam_longitude=-169.0, texture_width=4096,
                 warp_smoothing=0.0, coarse_step=8, band_rows=256, polar_ice_color=(255, 255, 255, 255),
                 polar_ice_latitude=-72.0, ice_below_map=True):
        self.map_path = map_path
        self.landmarks = landmarks
        self.seam_longitude = seam_longitude
        self.texture_width = texture_width
        self.texture_height = texture_width // 2
        self.warp_smoothing = warp_smoothing
        self.coarse_step = coarse_step
        self.band_rows = band_rows
        self.polar_ice_color = polar_ice_color
        self.polar_ice_latitude = polar_ice_latitude
        self.ice_below_map = ice_below_map
        self.ocean_color = None

    def _unwrap(self, longitude):
        return np.where(longitude < self.seam_longitude, longitude + 360.0, longitude)

    def _build_warp(self):
        geo_points = [(self._unwrap(longitude), latitude) for _, latitude, longitude, _, _ in self.landmarks]
        map_points = [(map_x, map_y) for _, _, _, map_x, map_y in self.landmarks]
        return ThinPlateWarp(geo_points, map_points, self.warp_smoothing)

    def _load_map(self):
        image = pygame.image.load(self.map_path)
        raw = pygame.image.tobytes(image, "RGBA", False)
        return np.frombuffer(raw, dtype=np.uint8).reshape(image.get_height(), image.get_width(), 4)

    def _seam_shift(self):
        return int(round((self.seam_longitude + 180.0) * self.texture_width / 360.0))

    def _column_longitudes(self, columns):
        degrees_per_column = 360.0 / self.texture_width
        return -180.0 + (columns + self._seam_shift() + 0.5) * degrees_per_column

    def _row_latitudes(self, rows):
        return 90.0 - (rows + 0.5) * 180.0 / self.texture_height

    @staticmethod
    def _linear_blend(coarse_axis, fine_axis):
        upper = np.clip(np.searchsorted(coarse_axis, fine_axis), 1, len(coarse_axis) - 1)
        lower = upper - 1
        fraction = (fine_axis - coarse_axis[lower]) / (coarse_axis[upper] - coarse_axis[lower])
        return lower, upper, fraction

    def _map_coordinates(self, warp):
        """Map pixel position for every texel, columns starting at the seam so longitude never jumps."""
        coarse_columns = np.linspace(0.0, self.texture_width - 1, self.texture_width // self.coarse_step + 1)
        coarse_rows = np.linspace(0.0, self.texture_height - 1, self.texture_height // self.coarse_step + 1)
        longitude_grid, latitude_grid = np.meshgrid(self._column_longitudes(coarse_columns),
                                                    self._row_latitudes(coarse_rows))
        geo_points = np.column_stack((longitude_grid.ravel(), latitude_grid.ravel()))
        coarse_map = warp(geo_points).reshape(len(coarse_rows), len(coarse_columns), 2)

        left, right, across = self._linear_blend(coarse_columns, np.arange(self.texture_width, dtype=np.float64))
        widened = coarse_map[:, left] * (1.0 - across)[None, :, None] + coarse_map[:, right] * across[None, :, None]
        top, bottom, down = self._linear_blend(coarse_rows, np.arange(self.texture_height, dtype=np.float64))
        full_map = widened[top] * (1.0 - down)[:, None, None] + widened[bottom] * down[:, None, None]
        return full_map[:, :, 0], full_map[:, :, 1]

    def _sample_band(self, source, map_x, map_y, latitudes, ocean_color):
        source_height, source_width = source.shape[:2]
        inside = (map_x >= 0.0) & (map_x <= source_width - 1) & (map_y >= 0.0) & (map_y <= source_height - 1)
        clamped_x = np.clip(map_x, 0.0, source_width - 1.001)
        clamped_y = np.clip(map_y, 0.0, source_height - 1.001)
        left = clamped_x.astype(np.int32)
        top = clamped_y.astype(np.int32)
        across = (clamped_x - left)[..., None]
        down = (clamped_y - top)[..., None]
        upper_row = source[top, left] * (1.0 - across) + source[top, left + 1] * across
        lower_row = source[top + 1, left] * (1.0 - across) + source[top + 1, left + 1] * across
        band = (upper_row * (1.0 - down) + lower_row * down).astype(np.uint8)
        band[~inside] = ocean_color
        frozen = (latitudes[:, None] < self.polar_ice_latitude) & np.all(band == ocean_color, axis=2)
        if self.ice_below_map:
            frozen |= map_y > source_height - 1
        band[frozen] = self.polar_ice_color
        return band

    def equirectangular(self):
        source = self._load_map()
        ocean_color = source[0, 0].copy()
        self.ocean_color = ocean_color
        map_x, map_y = self._map_coordinates(self._build_warp())
        latitudes = self._row_latitudes(np.arange(self.texture_height, dtype=np.float64))
        texture = np.empty((self.texture_height, self.texture_width, 4), dtype=np.uint8)
        for band_start in range(0, self.texture_height, self.band_rows):
            band = slice(band_start, band_start + self.band_rows)
            texture[band] = self._sample_band(source, map_x[band], map_y[band], latitudes[band], ocean_color)
        return np.roll(texture, self._seam_shift(), axis=1)

    def land_mask(self, texture):
        return np.any(texture != self.ocean_color, axis=2)


class HistoricalEarth(Earth):
    """Earth wearing a political map of a chosen year; show_year() switches maps instantly.

    Every year in `years` is reprojected up front (a few seconds), so switching later costs nothing.
    """

    def __init__(self, x, y, z, year=1936, years=None, maps=None, seam_longitude=-169.0, warp_smoothing=0.0,
                 **earth_options):
        self.maps = maps or HISTORICAL_MAPS
        self.years = tuple(years or self.maps)
        if year not in self.years:
            raise KeyError(f"No map for {year}; available years: {', '.join(map(str, self.years))}")
        self.year = year
        self.historical_maps = {map_year: self._historical_map(map_year, seam_longitude, warp_smoothing)
                                for map_year in self.years}
        self.surfaces = {}
        self.land_masks = {}
        self.fading_from = None
        self.fade_seconds = 0.0
        self.fade_progress = 1.0
        places = {name: (latitude, longitude) for name, latitude, longitude in PLACES}
        places.update(earth_options.pop("places", None) or {})
        super().__init__(x, y, z, texture_path=self.historical_maps[year].map_path, places=places, **earth_options)

    def _historical_map(self, year, seam_longitude, warp_smoothing):
        setup = self.maps[year]
        map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", setup["file"])
        geo ={name: (latitude, longitude) for name, latitude, longitude in PLACES}
        landmarks = tuple((name, *geo[name], *pixel) for name, pixel in setup["pixels"].items())
        return HistoricalMap(map_path, landmarks, seam_longitude=seam_longitude,
                             texture_width=setup["texture_width"], warp_smoothing=warp_smoothing,
                             polar_ice_latitude=setup["polar_ice_latitude"], ice_below_map=setup["ice_below_map"])

    def _load_surface(self, pixels=None):
        for map_year, historical_map in self.historical_maps.items():
            texture = historical_map.equirectangular()
            self.land_masks[map_year] = historical_map.land_mask(texture)
            self.surfaces[map_year] = super()._load_surface(np.ascontiguousarray(texture[::-1]))
        self.land = self.land_masks[self.year]
        return self.surfaces[self.year]

    def show_year(self, year, fade_seconds=0.0):
        """Switch to the year's map; with fade_seconds > 0 the new map dissolves in over the old one."""
        if year not in self.surfaces:
            raise KeyError(f"No map for {year}; available years: {', '.join(map(str, self.years))}")
        self.fading_from = self.surface if fade_seconds > 0.0 and year != self.year else None
        self.fade_seconds = fade_seconds
        self.fade_progress = 0.0 if self.fading_from is not None else 1.0
        self.year = year
        self.surface = self.surfaces[year]
        self.land = self.land_masks[year]
        self._replant_signs()

    def update(self, dt):
        super().update(dt)
        if self.fading_from is not None:
            self.fade_progress = min(1.0, self.fade_progress + dt / self.fade_seconds)
            if self.fade_progress >= 1.0:
                self.fading_from = None

    def _draw_surface(self):
        if self.fading_from is None:
            super()._draw_surface()
            return
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBindTexture(GL_TEXTURE_2D, self.fading_from.id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        gluSphere(self.quadric, self.radius, 48, 32)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthFunc(GL_LEQUAL)
        glBindTexture(GL_TEXTURE_2D, self.surface.id)
        glColor4f(1.0, 1.0, 1.0, self.fade_progress)
        gluSphere(self.quadric, self.radius, 48, 32)
        glDepthFunc(GL_LESS)
        glDisable(GL_BLEND)

    def _is_water(self, latitude, longitude):
        rows, columns = self.land.shape
        row = int(np.clip((90.0 - latitude) / 180.0 * rows, 0, rows - 1))
        column = int(((longitude + 180.0) % 360.0) / 360.0 * columns) % columns
        return not self.land[row, column]
