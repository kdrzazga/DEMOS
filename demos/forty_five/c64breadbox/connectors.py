import math

from OpenGL.GL import *

from demos.forty_five.c64breadbox.primitives import Box, Cylinder
from demos.forty_five.geometry import color, quad


class FacePlane:

	def __init__(self, face_centre, facing):
		self.face_centre = face_centre
		self.facing = facing

	def vector(self, along, across, up):
		if self.facing == "right":
			return along, up, across
		return -across, up, -along

	def point(self, along, across, up):
		face_x, face_y, face_z = self.face_centre
		offset_x, offset_y, offset_z = self.vector(along, across, up)
		return face_x + offset_x, face_y + offset_y, face_z + offset_z

	def axis(self):
		return "x" if self.facing == "right" else "z"

	def normal(self):
		return self.vector(1.0, 0.0, 0.0)


def face_plane_for(box_minimum, box_maximum, facing, centre_height):
	left, _, back = box_minimum
	right, _, front = box_maximum
	if facing == "right":
		return FacePlane((right, centre_height, (back + front) / 2), facing)
	return FacePlane(((left + right) / 2, centre_height, back), facing)


class DinSocket:

	def __init__(self, spec, photo, outer_radius_cm=0.72, inner_radius_cm=0.62, cavity_depth_cm=0.5,
	             pin_circle_radius_cm=0.35, hole_radius_cm=0.05, segments=40,
	             body_rgb=(25, 25, 25), shell_rgb=(38, 38, 40), insulator_rgb=(55, 55, 55), hole_rgb=(4, 4, 4)):
		self.spec = spec
		self.photo = photo
		self.outer_radius = outer_radius_cm
		self.inner_radius = inner_radius_cm
		self.cavity_depth = cavity_depth_cm
		self.pin_circle_radius = pin_circle_radius_cm
		self.hole_radius = hole_radius_cm
		self.segments = segments
		self.body_rgb = body_rgb
		self.shell_rgb = shell_rgb
		self.insulator_rgb = insulator_rgb
		self.hole_rgb = hole_rgb
		left, back, right, front = photo.world_rect(spec.rect)
		self.body = Box((left, 0.0, back), (right, spec.height_cm, front))
		self.face = face_plane_for(self.body.minimum, self.body.maximum, spec.facing, spec.height_cm / 2)
		self.shell = Cylinder(self.face.point(spec.protrusion_cm / 2, 0.0, 0.0), outer_radius_cm,
		                      spec.protrusion_cm, self.face.axis(), segments)

	def draw(self):
		self.body.draw(self.body_rgb, skip=("top",))
		self.body.draw_photo_top(self.photo)
		self.shell.draw(self.shell_rgb, caps=False)
		self._draw_front()

	def _angles(self):
		return [2.0 * math.pi * index / self.segments for index in range(self.segments + 1)]

	def _ring_point(self, along, angle, radius):
		return self.face.point(along, radius * math.sin(angle), radius * math.cos(angle))

	def _draw_front(self):
		front = self.spec.protrusion_cm
		floor = front - self.cavity_depth
		color(self.shell_rgb)
		glNormal3f(*self.face.normal())
		glBegin(GL_QUAD_STRIP)
		for angle in self._angles():
			glVertex3f(*self._ring_point(front, angle, self.outer_radius))
			glVertex3f(*self._ring_point(front, angle, self.inner_radius))
		glEnd()
		color(self.hole_rgb)
		glBegin(GL_QUAD_STRIP)
		for angle in self._angles():
			glNormal3f(*self.face.vector(0.0, -math.sin(angle), -math.cos(angle)))
			glVertex3f(*self._ring_point(front, angle, self.inner_radius))
			glVertex3f(*self._ring_point(floor, angle, self.inner_radius))
		glEnd()
		self._draw_disc(floor, 0.0, 0.0, self.inner_radius, self.insulator_rgb)
		for across, up in self._hole_positions():
			self._draw_disc(floor + 0.005, across, up, self.hole_radius, self.hole_rgb)

	def _hole_positions(self):
		positions = [(self.pin_circle_radius * math.sin(math.radians(angle)),
		              self.pin_circle_radius * math.cos(math.radians(angle)))
		             for angle in self.spec.pin_angles_degrees]
		if self.spec.has_centre_pin:
			positions.append((0.0, 0.0))
		return positions

	def _draw_disc(self, along, centre_across, centre_up, radius, rgb):
		color(rgb)
		glNormal3f(*self.face.normal())
		glBegin(GL_TRIANGLE_FAN)
		glVertex3f(*self.face.point(along, centre_across, centre_up))
		for angle in self._angles():
			glVertex3f(*self.face.point(along, centre_across + radius * math.sin(angle),
			                            centre_up + radius * math.cos(angle)))
		glEnd()


class ControlPort:

	def __init__(self, spec, photo, shell_top_width_cm=1.63, shell_bottom_width_cm=1.35, shell_height_cm=0.8,
	             shell_wall_cm=0.06, cavity_depth_cm=0.5, flange_thickness_cm=0.08, pin_pitch_cm=0.277,
	             pin_row_spacing_cm=0.284, pin_half_size_cm=0.04, pin_length_cm=0.3,
	             body_rgb=(30, 30, 32), shell_rgb=(185, 185, 180), insulator_rgb=(22, 22, 22), pin_rgb=(205, 180, 110)):
		self.spec = spec
		self.photo = photo
		self.shell_top_width = shell_top_width_cm
		self.shell_bottom_width = shell_bottom_width_cm
		self.shell_height = shell_height_cm
		self.shell_wall = shell_wall_cm
		self.cavity_depth = cavity_depth_cm
		self.pin_pitch = pin_pitch_cm
		self.pin_row_spacing = pin_row_spacing_cm
		self.pin_half_size = pin_half_size_cm
		self.pin_length = pin_length_cm
		self.body_rgb = body_rgb
		self.shell_rgb = shell_rgb
		self.insulator_rgb = insulator_rgb
		self.pin_rgb = pin_rgb
		left, back, right, front = photo.world_rect(spec.rect)
		self.body = Box((left, 0.0, back), (right - flange_thickness_cm, spec.height_cm, front))
		self.flange = Box((right - flange_thickness_cm, 0.0, back - 0.02), (right, spec.height_cm + 0.02, front + 0.02))
		self.face = FacePlane((right, spec.height_cm / 2, (back + front) / 2), "right")

	def draw(self):
		self.body.draw(self.body_rgb, skip=("top",))
		self.body.draw_photo_top(self.photo)
		self.flange.draw(self.shell_rgb)
		self._draw_shell()
		self._draw_pins()

	def _trapezoid(self, along, inset):
		half_top = self.shell_top_width / 2 - inset
		half_bottom = self.shell_bottom_width / 2 - inset
		half_height = self.shell_height / 2 - inset
		return (self.face.point(along, -half_bottom, -half_height), self.face.point(along, half_bottom, -half_height),
		        self.face.point(along, half_top, half_height), self.face.point(along, -half_top, half_height))

	def _draw_shell(self):
		length = self.spec.shell_length_cm
		outer_start = self._trapezoid(0.0, 0.0)
		outer_end = self._trapezoid(length, 0.0)
		inner_end = self._trapezoid(length, self.shell_wall)
		inner_floor = self._trapezoid(length - self.cavity_depth, self.shell_wall)
		color(self.shell_rgb)
		glBegin(GL_QUADS)
		for index in range(4):
			following = (index + 1) % 4
			quad(outer_start[index], outer_start[following], outer_end[following], outer_end[index])
			quad(outer_end[index], outer_end[following], inner_end[following], inner_end[index])
			quad(inner_end[index], inner_end[following], inner_floor[following], inner_floor[index])
		glEnd()
		color(self.insulator_rgb)
		glBegin(GL_QUADS)
		quad(*inner_floor)
		glEnd()

	def _draw_pins(self):
		floor = self.spec.shell_length_cm - self.cavity_depth
		rows = ((5, self.pin_row_spacing / 2), (4, -self.pin_row_spacing / 2))
		for pin_count, up in rows:
			for index in range(pin_count):
				across = (index - (pin_count - 1) / 2) * self.pin_pitch
				near = self.face.point(floor, across - self.pin_half_size, up - self.pin_half_size)
				far = self.face.point(floor + self.pin_length, across + self.pin_half_size, up + self.pin_half_size)
				Box(near, far).draw(self.pin_rgb)


class PowerSwitch:

	def __init__(self, spec, photo, paddle_thickness_cm=0.25, paddle_fill=0.8,
	             body_rgb=(45, 75, 175), housing_rgb=(28, 28, 28), paddle_rgb=(42, 42, 42)):
		self.spec = spec
		self.photo = photo
		self.paddle_thickness = paddle_thickness_cm
		self.paddle_fill = paddle_fill
		self.body_rgb = body_rgb
		self.housing_rgb = housing_rgb
		self.paddle_rgb = paddle_rgb
		body_left, body_back, body_right, body_front = photo.world_rect(spec.body_rect)
		self.body = Box((body_left, 0.0, body_back), (body_right, spec.body_height_cm, body_front))
		left, back, right, front = photo.world_rect(spec.housing_rect)
		self.housing = Box((left, 0.0, back), (right, spec.housing_height_cm, front))

	def draw(self):
		self.body.draw(self.body_rgb, skip=("top",))
		self.body.draw_photo_top(self.photo)
		self.housing.draw(self.housing_rgb, skip=("top",))
		self.housing.draw_photo_top(self.photo)
		self._draw_paddle()

	def _draw_paddle(self):
		_, _, back = self.housing.minimum
		right, height, front = self.housing.maximum
		half_height = height * self.paddle_fill / 2
		half_width = (front - back) * self.paddle_fill / 2
		glPushMatrix()
		glTranslatef(right, height / 2, (back + front) / 2)
		glRotatef(self.spec.paddle_tilt_degrees, 0.0, 0.0, 1.0)
		Box((-self.paddle_thickness / 2, -half_height, -half_width),
		    (self.paddle_thickness / 2, half_height, half_width)).draw(self.paddle_rgb)
		glPopMatrix()
