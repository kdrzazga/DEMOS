"""3D models of the Kickstart 2.0 "insert disk" screen: rainbow checkmark, floppy drive and floppy disk.

Coordinates come from the 450x360 reference video (a600.mp4): 1 world unit = 100 reference pixels,
origin at screen centre. Colours were sampled from the video.
"""
from demos.amiga.common.meshes import box_triangles, colored_mesh, extruded_polygon_triangles, translated

REFERENCE_SIZE = (450, 360)


def ref_to_world(px, py):
	return (px - REFERENCE_SIZE[0] / 2) / 100.0, (REFERENCE_SIZE[1] / 2 - py) / 100.0


def lerp(a, b, t):
	return tuple(x + (y - x) * t for x, y in zip(a, b))


def gradient(stops):
	"""stops: ((world_y, rgb), ...) sorted by y. Returns color_at(x, y)."""
	def color_at(_x, y):
		if y <= stops[0][0]:
			return stops[0][1]
		for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
			if y <= y1:
				return lerp(c0, c1, (y - y0) / (y1 - y0))
		return stops[-1][1]
	return color_at


def counter_clockwise(points):
	area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
	return points if area > 0 else points[::-1]


# --------------------------------------------------------------------------- rainbow checkmark

class CheckmarkModel:
	"""Two parallel check strokes (each a short blue arm and a long green-to-red arm), extruded."""

	def __init__(self, strand_offsets_px=(0.0, 15.0), z_front=0.0, depth=0.08, slices=16):
		self.strand_offsets_px = strand_offsets_px
		self.z_front = z_front
		self.depth = depth
		self.slices = slices
		# reference-pixel corners of one strand: arm = (start edge, end edge), each edge = (left, right)
		self.short_arm = (((73.5, 159), (86.0, 159)), ((92.5, 190), (106.5, 190)))
		self.long_arm = (((92.5, 190), (107.5, 190)), ((148.5, 95), (161.0, 95)))
		self.long_colors = gradient(tuple((ref_to_world(0, py)[1], rgb) for py, rgb in (
			(190, (0.00, 0.68, 0.00)), (170, (0.23, 0.72, 0.00)), (130, (0.82, 0.62, 0.00)),
			(112, (0.85, 0.28, 0.00)), (95, (0.89, 0.06, 0.00)))))
		self.short_colors = gradient(tuple((ref_to_world(0, py)[1], rgb) for py, rgb in (
			(190, (0.00, 0.60, 0.45)), (159, (0.00, 0.26, 0.76)))))

	def _arm_triangles(self, arm, offset_px, color_at, z_shift):
		(start_left, start_right), (end_left, end_right) = arm
		triangles = []
		for index in range(self.slices):
			t0, t1 = index / self.slices, (index + 1) / self.slices
			corners_px = (lerp(start_left, end_left, t0), lerp(start_right, end_right, t0),
				lerp(start_right, end_right, t1), lerp(start_left, end_left, t1))
			corners = counter_clockwise([ref_to_world(px + offset_px, py) for px, py in corners_px])
			triangles += extruded_polygon_triangles(corners, self.z_front + z_shift,
				self.z_front - self.depth + z_shift, color_at)
		return triangles

	def build(self):
		triangles = []
		for offset in self.strand_offsets_px:
			triangles += self._arm_triangles(self.long_arm, offset, self.long_colors, 0.0)
			# tucked a hair behind so the overlap at the bottom of the V doesn't z-fight
			triangles += self._arm_triangles(self.short_arm, offset, self.short_colors, -0.004)
		return colored_mesh(triangles)


# --------------------------------------------------------------------------- floppy drive

DRIVE_COLOR = (0.76, 0.55, 0.42)
SLOT_COLOR = (0.0, 0.0, 0.0)


class DriveModel:
	"""External drive seen from the front. The slot is a real opening in a thin front panel with a
	black backing just behind it, so the disk visibly slides in and vanishes into the dark."""

	def __init__(self, center=ref_to_world(350.5, 170.0), width=0.99, height=0.25, depth=1.0, panel_depth=0.04,
			slot_x=(-0.445, 0.445), slot_y=(0.035, 0.09)):
		self.center = center
		self.width = width
		self.height = height
		self.depth = depth
		self.panel_depth = panel_depth
		self.slot_x = slot_x
		self.slot_y = slot_y

	@property
	def slot_center(self):
		"""World (x, y) of the slot mouth centre."""
		return self.center[0] + sum(self.slot_x) / 2, self.center[1] + sum(self.slot_y) / 2

	def build(self):
		half_w, half_h = self.width / 2, self.height / 2
		(slot_left, slot_right), (slot_bottom, slot_top) = self.slot_x, self.slot_y
		panel = -self.panel_depth
		triangles = []
		# front panel around the slot opening
		for (x0, y0), (x1, y1) in (((-half_w, slot_top), (half_w, half_h)), ((-half_w, -half_h), (half_w, slot_bottom)),
				((-half_w, slot_bottom), (slot_left, slot_top)), ((slot_right, slot_bottom), (half_w, slot_top))):
			triangles += box_triangles((x0, y0, panel), (x1, y1, 0.0), DRIVE_COLOR)
		triangles += box_triangles((-half_w, -half_h, -self.depth), (half_w, half_h, panel), DRIVE_COLOR)
		triangles += box_triangles((slot_left, slot_bottom, panel - 0.002), (slot_right, slot_top, panel + 0.002), SLOT_COLOR)
		# activity LED and eject button (a lighter frame with a drive-coloured face)
		triangles += box_triangles((-0.345, -0.066, 0.0), (-0.29, -0.054, 0.004), (0.12, 0.06, 0.06))
		triangles += box_triangles((0.255, -0.06, 0.0), (0.41, -0.025, 0.006), (0.88, 0.68, 0.55))
		triangles += box_triangles((0.262, -0.054, 0.0), (0.403, -0.031, 0.008), DRIVE_COLOR)
		return colored_mesh(translated(triangles, (*self.center, 0.0)))


# --------------------------------------------------------------------------- floppy disk

DISK_BLUE = (0.09, 0.16, 0.44)


class FloppyModel:
	"""3.5" disk in local coordinates: the top (shutter) edge centre is the origin, the disk hangs
	down -y and its label faces +z. Rotating -90 degrees around x lays it flat, shutter first."""

	def __init__(self, width=0.85, height=0.76, thickness=0.03):
		self.width = width
		self.height = height
		self.thickness = thickness

	def build(self):
		half_w, half_t = self.width / 2, self.thickness / 2
		face = half_t
		triangles = box_triangles((-half_w, -self.height, -half_t), (half_w, 0.0, half_t), DISK_BLUE)
		triangles += box_triangles((-half_w, -self.height, face), (-half_w + 0.06, 0.0, face + 0.002), (0.06, 0.10, 0.32))
		for z0, z1 in ((face, face + 0.006), (-face - 0.006, -face)):   # metal shutter wraps both sides
			triangles += box_triangles((-0.205, -0.26, z0), (0.255, 0.0, z1), (0.48, 0.42, 0.37))
		triangles += box_triangles((0.055, -0.225, face), (0.115, -0.05, face + 0.008), (0.09, 0.11, 0.31))
		triangles += box_triangles((-0.315, -self.height, face), (0.345, -0.34, face + 0.003), (0.79, 0.79, 0.79))
		for y in (-0.055, -0.725):   # write-protect / density holes
			triangles += box_triangles((-0.415, y, face), (-0.385, y + 0.03, face + 0.004), (0.03, 0.03, 0.08))
		return colored_mesh(triangles)
