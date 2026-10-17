"""The scanned drawing and what can be read from its pixels."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class Drawing:
    """A hand drawing scanned on squared paper.

    The grid mesh is light grey and the ink is near-black, so a luminance ramp
    separates them: brighter than ``paper_luminance`` is paper (mesh included),
    darker than ``ink_luminance`` is full ink, antialiased edges blend between.
    """

    def __init__(self, path, ink_luminance=90, paper_luminance=170):
        self.scan_rgb = np.asarray(Image.open(path).convert("RGB"))
        self.height, self.width = self.scan_rgb.shape[:2]
        luminance = self.scan_rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
        self.ink = np.clip((paper_luminance - luminance) / (paper_luminance - ink_luminance), 0.0, 1.0)

    @property
    def size(self):
        return self.width, self.height

    def clean_rgb(self):
        grey = (255 * (1.0 - self.ink)).astype(np.uint8)
        return np.repeat(grey[:, :, None], 3, axis=2)

    def top_of_ink(self, x, band_top, band_bottom, threshold=0.5):
        """Walk down a pixel column from band_top; return the first y that hits ink."""
        x = int(round(min(max(x, 1), self.width - 2)))
        column = self.ink[int(band_top):int(band_bottom), x - 1:x + 2].max(axis=1)
        hits = np.nonzero(column > threshold)[0]
        return band_top + hits[0] if len(hits) else band_bottom

    def swelling(self, zone, barriers, grow_pixels, plateau_pixels, downscale=2, blur_passes=2):
        """Height map in [0, 1] for the area inside ``zone``: 0 on ink lines, on the zone
        border and on the (grown) ``barriers``, rising with a round shoulder to 1 at
        ``plateau_pixels`` away from them. Every region enclosed by ink becomes a
        rounded, flat-topped block. Returned at 1/downscale resolution."""
        free = Image.new("L", self.size, 0)
        draw = ImageDraw.Draw(free)
        draw.polygon([(float(x), float(y)) for x, y in zone], fill=255)
        blocked = Image.new("L", self.size, 0)
        blocked_draw = ImageDraw.Draw(blocked)
        for barrier in barriers:
            blocked_draw.polygon([(float(x), float(y)) for x, y in barrier], fill=255)
        blocked = np.asarray(blocked.filter(ImageFilter.MaxFilter(2 * grow_pixels + 1))) > 0
        free_pixels = (np.asarray(free) > 0) & ~blocked & (self.ink < 0.5)

        small_size = (self.width // downscale, self.height // downscale)
        shrinking = Image.fromarray((free_pixels * 255).astype(np.uint8)).resize(small_size, Image.BILINEAR)
        shrinking = shrinking.point(lambda value: 255 if value > 127 else 0)
        steps = max(1, plateau_pixels // downscale)
        distance = np.zeros((small_size[1], small_size[0]), np.float32)
        for _ in range(steps):  # each erosion peels one pixel: survivors count = distance
            distance += np.asarray(shrinking, np.float32) / 255.0
            shrinking = shrinking.filter(ImageFilter.MinFilter(3))
        from_edge = distance / steps
        height = np.sqrt(1.0 - (1.0 - from_edge) ** 2)
        for _ in range(blur_passes):
            padded = np.pad(height, 1, mode="edge")
            height = sum(padded[1 + dy:padded.shape[0] - 1 + dy, 1 + dx:padded.shape[1] - 1 + dx]
                         for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
        return height, downscale

    def ink_outside(self, footprints, grow_pixels):
        """Ink coverage with the given polygons (slightly grown) cut away."""
        mask = Image.new("L", self.size, 0)
        draw = ImageDraw.Draw(mask)
        for footprint in footprints:
            draw.polygon([(float(x), float(y)) for x, y in footprint], fill=255)
        mask = mask.filter(ImageFilter.MaxFilter(2 * grow_pixels + 1))
        inside = np.asarray(mask, np.float32) / 255.0
        return self.ink * (1.0 - inside)
