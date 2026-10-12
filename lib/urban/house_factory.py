from lib.urban.detailed_house import DetailedHouse
from lib.urban.house import House
from lib.urban.shapes import Shapes
from lib.urban.textures import TextureFactory


class SimpleHouseFactory:
    def create(self, x, y, z, floor_count, windows_per_floor=3, **options):
        return House(x, y, z, floor_count, windows_per_floor, **options)


class DetailedHouseFactory:
    def __init__(self):
        self.shapes = None
        self.roof_texture = None

    def _prepare(self):
        if self.shapes is None:
            self.shapes = Shapes()
            textures = TextureFactory()
            self.roof_texture = textures.upload(textures.roof_tiles())

    def create(self, x, y, z, floor_count, windows_per_floor=3, **options):
        self._prepare()
        return DetailedHouse(x, y, z, floor_count, windows_per_floor, shapes=self.shapes,
                             roof_texture=self.roof_texture, **options)


class HouseFactories:
    def __init__(self):
        self.makers = {"simple": SimpleHouseFactory, "detailed": DetailedHouseFactory}

    def create(self, style):
        if style not in self.makers:
            raise ValueError(f"Unknown house style '{style}', expected one of {sorted(self.makers)}")
        return self.makers[style]()
