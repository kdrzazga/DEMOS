import os

import numpy as np
import pygame

from lib.earth import Earth


# (name, latitude, longitude, map x, map y): coastline extremes and cities located on world1936.png.
# The map is hand drawn, not a true projection, so it is warped onto the globe through these points.
WORLD1936_LANDMARKS = (
    ("Cape Agulhas", -34.83, 20.00, 2095, 1794),
    ("Cape Horn", -55.98, -67.27, 1089, 2105),
    ("South East Cape", -43.64, 146.83, 3784, 1888),
    ("Kanyakumari", 8.08, 77.54, 2890, 1126),
    ("Dondra Head", 5.92, 80.59, 2933, 1165),
    ("Ponta do Seixas", -7.15, -34.79, 1356, 1360),
    ("Cap-Vert", 14.73, -17.53, 1593, 1024),
    ("Ras Hafun", 10.44, 51.41, 2532, 1069),
    ("Cabo da Roca", 38.78, -9.50, 1718, 647),
    ("Cape Byron", -28.64, 153.64, 3901, 1619),
    ("Steep Point", -26.15, 113.16, 3411, 1618),
    ("North Cape", 71.18, 25.78, 2120, 181),
    ("Cape Morris Jesup", 83.66, -33.40, 1620, 39),
    ("Antarctic Peninsula", -63.20, -57.00, 1282, 2137),
    ("Cape Prince of Wales", 65.60, -168.10, 19, 392),
    ("Cape Dezhnev", 66.08, -169.66, 3828, 268),
    ("Florida Keys", 25.12, -81.08, 755, 858),
    ("Cabo San Lucas", 22.88, -109.90, 359, 882),
    ("Punta Parinas", -4.68, -81.33, 713, 1324),
    ("Cape Spear", 47.52, -52.62, 1209, 486),
    ("Point Barrow", 71.39, -156.50, 349, 182),
    ("Cape Lopatka", 50.87, 156.67, 3704, 459),
    ("Ca Mau", 8.60, 104.70, 3271, 1116),
    ("Cape Sainte Marie", -25.60, 45.15, 2438, 1653),
    ("Cap d'Ambre", -11.95, 49.26, 2503, 1441),
    ("Stewart Island", -47.30, 167.50, 4013, 2041),
    ("North Cape NZ", -34.40, 173.00, 4193, 1851),
    ("Cape Mendocino", 40.44, -124.40, 265, 648),
    ("Cape Farewell", 59.77, -43.90, 1376, 326),
    ("Dunmore Head", 52.10, -10.48, 1728, 443),
    ("Cape Chidley", 60.40, -64.40, 1148, 338),
    ("Cape Palmas", 4.37, -7.73, 1699, 1169),
    ("Lodz", 51.76, 19.46, 2080, 448),
    ("Auschwitz", 50.03, 19.20, 2072, 476),
    ("Bergen-Belsen", 52.76, 9.91, 1969, 434),
    ("New York", 40.71, -74.01, 907, 617),
    ("Toronto", 43.65, -79.38, 863, 573),
    ("Monte Sereno", 37.24, -121.99, 277, 692),
)


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
    """Reprojects a hand-drawn world map into an equirectangular texture (north up, longitude -180 at left)."""

    def __init__(self, map_path, landmarks, seam_longitude=-169.0, texture_width=4096,
                 warp_smoothing=0.0, coarse_step=8, band_rows=256, polar_ice_color=(255, 255, 255, 255),
                 polar_ice_latitude=-72.0):
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
        open_polar_sea = (latitudes[:, None] < self.polar_ice_latitude) & np.all(band == ocean_color, axis=2)
        band[(map_y > source_height - 1) | open_polar_sea] = self.polar_ice_color
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


class Earth1936(Earth):
    """Earth wearing the political map of 1936."""

    def __init__(self, x, y, z, texture_path=None, landmarks=WORLD1936_LANDMARKS, seam_longitude=-169.0,
                 texture_width=4096, warp_smoothing=0.0, **earth_options):
        self.historical_map = HistoricalMap(
            texture_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "world1936.png"),
            landmarks, seam_longitude=seam_longitude, texture_width=texture_width, warp_smoothing=warp_smoothing)
        places = {name: (latitude, longitude) for name, latitude, longitude, _, _ in landmarks}
        places.update(earth_options.pop("places", None) or {})
        super().__init__(x, y, z, texture_path=self.historical_map.map_path, places=places, **earth_options)

    def _surface_pixels(self):
        texture = self.historical_map.equirectangular()
        self.land = np.any(texture != self.historical_map.ocean_color, axis=2)
        return np.ascontiguousarray(texture[::-1])

    def _is_water(self, latitude, longitude):
        rows, columns = self.land.shape
        row = int(np.clip((90.0 - latitude) / 180.0 * rows, 0, rows - 1))
        column = int(((longitude + 180.0) % 360.0) / 360.0 * columns) % columns
        return not self.land[row, column]
