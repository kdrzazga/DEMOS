from OpenGL.GL import *

from demos.forty_five.c64breadbox.primitives import Box, Cylinder


class PrintedCircuitBoard:

	def __init__(self, photo, outline, thickness_cm, edge_rgb, alpha_cutoff=0.5):
		self.photo = photo
		self.outline = outline
		self.thickness = thickness_cm
		self.edge_rgb = edge_rgb
		self.alpha_cutoff = alpha_cutoff

	def draw(self):
		for rect in self.outline:
			left, back, right, front = self.photo.world_rect(rect)
			Box((left, -self.thickness, back), (right, 0.0, front)).draw(self.edge_rgb, skip=("top",))
		half_width = self.photo.length(self.photo.width_px) / 2
		half_depth = self.photo.length(self.photo.height_px) / 2
		glEnable(GL_ALPHA_TEST)
		glAlphaFunc(GL_GREATER, self.alpha_cutoff)
		self.photo.begin()
		glBegin(GL_QUADS)
		glNormal3f(0.0, 1.0, 0.0)
		for corner_x, corner_z in ((-half_width, -half_depth), (-half_width, half_depth),
		                           (half_width, half_depth), (half_width, -half_depth)):
			self.photo.vertex(corner_x, 0.0, corner_z)
		glEnd()
		self.photo.end()
		glDisable(GL_ALPHA_TEST)


class PhotoBlock:

	def __init__(self, spec, photo):
		self.spec = spec
		self.photo = photo
		left, back, right, front = photo.world_rect(spec.rect)
		self.box = Box((left, 0.0, back), (right, spec.height_cm, front))

	def draw(self):
		self.box.draw(self.spec.side_rgb, skip=("top", "bottom"))
		self.box.draw_photo_top(self.photo)


class CylinderPart:

	def __init__(self, spec, photo):
		self.spec = spec
		self.photo = photo
		left, back, right, front = photo.world_rect(spec.rect)
		if spec.axis == "x":
			length, radius = right - left, (front - back) / 2
		else:
			length, radius = front - back, (right - left) / 2
		centre_height = radius if spec.centre_height_cm is None else spec.centre_height_cm
		self.cylinder = Cylinder(((left + right) / 2, centre_height, (back + front) / 2), radius, length, spec.axis)

	def draw(self):
		if self.spec.photo_textured:
			self.cylinder.draw(photo=self.photo)
		else:
			self.cylinder.draw(self.spec.rgb)


class Fuse:

	def __init__(self, spec, photo, glass_radius_ratio=0.85, filament_radius_ratio=0.06, filament_rgb=(150, 150, 150)):
		self.spec = spec
		self.filament_rgb = filament_rgb
		left, back, right, front = photo.world_rect(spec.rect)
		radius = (front - back) / 2
		centre_y = radius + spec.lift_cm
		centre_z = (back + front) / 2
		cap_length = photo.length(spec.cap_length_px)
		glass_length = right - left - 2 * cap_length
		self.caps = (
			Cylinder((left + cap_length / 2, centre_y, centre_z), radius, cap_length, "x"),
			Cylinder((right - cap_length / 2, centre_y, centre_z), radius, cap_length, "x"),
		)
		self.glass = Cylinder(((left + right) / 2, centre_y, centre_z), radius * glass_radius_ratio, glass_length, "x")
		self.filament = Cylinder(((left + right) / 2, centre_y, centre_z), radius * filament_radius_ratio,
		                         glass_length, "x", segments=8)

	def draw_opaque(self):
		for cap in self.caps:
			cap.draw(self.spec.cap_rgb)
		self.filament.draw(self.filament_rgb)

	def draw_glass(self):
		self.glass.draw(self.spec.glass_rgb, alpha=self.spec.glass_alpha, caps=False)
