import math
from dataclasses import dataclass

from OpenGL.GL import *

from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.c64breadbox.primitives import Box
from demos.forty_five.geometry import color

PIN1_END_YAW_DEGREES = {"top": 0.0, "right": -90.0, "bottom": 180.0, "left": 90.0}


@dataclass(frozen=True)
class SocketSeat:
	name: str
	chip_name: str
	package: DilPackage
	centre: tuple
	yaw_degrees: float
	pin1_end: str
	seat_height: float
	contact_depth: float
	insertion_axis: tuple = (0.0, -1.0, 0.0)

	def to_world(self, local_x, y, local_z):
		yaw = math.radians(self.yaw_degrees)
		centre_x, _, centre_z = self.centre
		return (centre_x + local_x * math.cos(yaw) + local_z * math.sin(yaw),
		        y,
		        centre_z - local_x * math.sin(yaw) + local_z * math.cos(yaw))

	def contact_positions(self):
		return tuple(self.to_world(local_x, self.centre[1], local_z)
		             for local_x, local_z in self.package.pin_positions())


class DilSocket:

	def __init__(self, spec, photo, height_cm=0.45, end_margin_cm=0.065, rail_width_cm=0.26,
	             end_bar_cm=0.15, floor_height_cm=0.08, contact_depth_cm=0.3, seat_gap_cm=0.05,
	             hole_half_size_cm=0.05, body_rgb=(32, 32, 34), floor_rgb=(14, 14, 15), contact_rgb=(90, 90, 90),
	             hole_rgb=(5, 5, 5)):
		self.spec = spec
		self.hole_half_size = hole_half_size_cm
		self.package = spec.package
		self.height = height_cm
		self.rail_width = rail_width_cm
		self.end_bar = end_bar_cm
		self.floor_height = floor_height_cm
		self.body_rgb = body_rgb
		self.floor_rgb = floor_rgb
		self.contact_rgb = contact_rgb
		self.hole_rgb = hole_rgb
		self.length = self.package.pins_per_side * self.package.pitch_cm + 2 * end_margin_cm
		self.width = self.package.row_spacing_cm + rail_width_cm
		centre_x, centre_z = photo.to_world(*spec.center_px)
		self.seat = SocketSeat(
			name=spec.name,
			chip_name=spec.chip_name,
			package=self.package,
			centre=(centre_x, height_cm, centre_z),
			yaw_degrees=PIN1_END_YAW_DEGREES[spec.pin1_end],
			pin1_end=spec.pin1_end,
			seat_height=height_cm + seat_gap_cm,
			contact_depth=contact_depth_cm)

	def draw(self):
		centre_x, _, centre_z = self.seat.centre
		glPushMatrix()
		glTranslatef(centre_x, 0.0, centre_z)
		glRotatef(self.seat.yaw_degrees, 0.0, 1.0, 0.0)
		self._draw_body()
		self._draw_contacts()
		glPopMatrix()

	def _draw_body(self):
		half_length, half_width = self.length / 2, self.width / 2
		inner_half_width = half_width - self.rail_width
		notch_half_width = min(0.15, inner_half_width * 0.4)
		Box((-half_width, 0.0, -half_length), (half_width, self.floor_height, half_length)).draw(self.floor_rgb)
		for body_part in (
				Box((-half_width, 0.0, -half_length), (-inner_half_width, self.height, half_length)),
				Box((inner_half_width, 0.0, -half_length), (half_width, self.height, half_length)),
				Box((-inner_half_width, 0.0, -half_length), (-notch_half_width, self.height, -half_length + self.end_bar)),
				Box((notch_half_width, 0.0, -half_length), (inner_half_width, self.height, -half_length + self.end_bar)),
				Box((-notch_half_width, 0.0, -half_length), (notch_half_width, self.height * 0.55, -half_length + self.end_bar)),
				Box((-inner_half_width, 0.0, half_length - self.end_bar), (inner_half_width, self.height, half_length)),
		) + self._cross_bars(half_length, inner_half_width):
			body_part.draw(self.body_rgb, skip=("bottom",))

	def _cross_bars(self, half_length, inner_half_width):
		count = max(1, self.package.pins_per_side // 7)
		half_thickness = 0.05
		bars = []
		for index in range(1, count + 1):
			bar_z = -half_length + 2 * half_length * index / (count + 1)
			bars.append(Box((-inner_half_width, 0.0, bar_z - half_thickness),
			                (inner_half_width, self.height * 0.6, bar_z + half_thickness)))
		return tuple(bars)

	def _contact_corners(self, pin_x, pin_z, y):
		half_size = self.hole_half_size
		return ((pin_x - half_size, y, pin_z - half_size), (pin_x - half_size, y, pin_z + half_size),
		        (pin_x + half_size, y, pin_z + half_size), (pin_x + half_size, y, pin_z - half_size))

	def _draw_contacts(self):
		hole_y, outline_y = self.height + 0.002, self.height + 0.004
		color(self.hole_rgb)
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for pin_x, pin_z in self.package.pin_positions():
			for corner in self._contact_corners(pin_x, pin_z, hole_y):
				glVertex3f(*corner)
		glEnd()
		glDisable(GL_LIGHTING)
		glLineWidth(1.0)
		color(self.contact_rgb)
		for pin_x, pin_z in self.package.pin_positions():
			glBegin(GL_LINE_LOOP)
			for corner in self._contact_corners(pin_x, pin_z, outline_y):
				glVertex3f(*corner)
			glEnd()
		glEnable(GL_LIGHTING)
