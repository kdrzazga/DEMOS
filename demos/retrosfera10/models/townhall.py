import math
import random

import pygame
from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GL_COMPILE, GL_ENABLE_BIT, GL_FRONT_AND_BACK, GL_LIGHTING,
	GL_LIGHTING_BIT, GL_LIGHT_MODEL_TWO_SIDE, GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR, GL_NORMALIZE, GL_REPEAT,
	GL_RGBA, GL_TEXTURE_2D, GL_TEXTURE_BIT, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S,
	GL_TEXTURE_WRAP_T, GL_TRIANGLES, GL_TRUE, GL_UNSIGNED_BYTE, glBegin, glBindTexture, glCallList,
	glColor3f, glColorMaterial, glDeleteLists, glDeleteTextures, glDisable, glEnable, glEnd, glEndList,
	glGenLists, glGenTextures, glLightModeli, glNewList, glNormal3f, glPopAttrib, glPushAttrib,
	glTexCoord2f, glTexParameteri, glVertex3f,
)
from OpenGL.GLU import gluBuild2DMipmaps


class Vector3:
	__slots__ = ("x", "y", "z")

	def __init__(self, x, y, z):
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)

	@classmethod
	def up(cls):
		return cls(0.0, 1.0, 0.0)

	def __add__(self, other):
		return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

	def __sub__(self, other):
		return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

	def __mul__(self, scalar):
		return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

	__rmul__ = __mul__

	def __neg__(self):
		return Vector3(-self.x, -self.y, -self.z)

	def dot(self, other):
		return self.x * other.x + self.y * other.y + self.z * other.z

	def cross(self, other):
		return Vector3(
			self.y * other.z - self.z * other.y,
			self.z * other.x - self.x * other.z,
			self.x * other.y - self.y * other.x,
		)

	def length(self):
		return math.sqrt(self.dot(self))

	def normalized(self):
		length = self.length()
		if length < 1e-9:
			return Vector3.up()
		return Vector3(self.x / length, self.y / length, self.z / length)

	def at_height(self, height):
		return Vector3(self.x, height, self.z)

	def is_close_to(self, other):
		return (self - other).length() < 1e-6


class ProceduralTexture:
	def __init__(self, width, height, span_u, span_v):
		self.width = width
		self.height = height
		self.span_u = span_u
		self.span_v = span_v
		self.texture_id = None

	def paint(self, surface):
		raise NotImplementedError

	def upload(self):
		surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
		self.paint(surface)
		pixels = pygame.image.tobytes(surface, "RGBA", True)
		self.texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
		return self

	def release(self):
		if self.texture_id is not None:
			glDeleteTextures([self.texture_id])
			self.texture_id = None


class SgraffitoTexture(ProceduralTexture):
	def __init__(self, block_width=0.9, block_height=0.45):
		super().__init__(128, 64, block_width * 2, block_height * 2)
		self.block_pixel_width = 64
		self.block_pixel_height = 32
		self.mortar_color = (150, 150, 146, 255)
		self.top_facet_color = (246, 245, 240, 255)
		self.left_facet_color = (214, 213, 207, 255)
		self.right_facet_color = (132, 132, 128, 255)
		self.bottom_facet_color = (104, 104, 101, 255)
		self.face_color = (236, 234, 228, 255)

	def paint(self, surface):
		surface.fill(self.mortar_color)
		for row in range(2):
			shift = (self.block_pixel_width // 2) * row
			for column in range(-1, 3):
				left = column * self.block_pixel_width + shift
				top = row * self.block_pixel_height
				self.paint_block(surface, left, top)

	def paint_block(self, surface, left, top):
		gap = 2
		bevel_x = 11
		bevel_y = 7
		outer_left = left + gap
		outer_top = top + gap
		outer_right = left + self.block_pixel_width - gap
		outer_bottom = top + self.block_pixel_height - gap
		inner_left = outer_left + bevel_x
		inner_right = outer_right - bevel_x
		inner_top = outer_top + bevel_y
		inner_bottom = outer_bottom - bevel_y
		pygame.draw.polygon(surface, self.top_facet_color, [
			(outer_left, outer_top), (outer_right, outer_top), (inner_right, inner_top), (inner_left, inner_top)])
		pygame.draw.polygon(surface, self.bottom_facet_color, [
			(outer_left, outer_bottom), (outer_right, outer_bottom), (inner_right, inner_bottom), (inner_left, inner_bottom)])
		pygame.draw.polygon(surface, self.left_facet_color, [
			(outer_left, outer_top), (inner_left, inner_top), (inner_left, inner_bottom), (outer_left, outer_bottom)])
		pygame.draw.polygon(surface, self.right_facet_color, [
			(outer_right, outer_top), (inner_right, inner_top), (inner_right, inner_bottom), (outer_right, outer_bottom)])
		surface.fill(self.face_color, pygame.Rect(inner_left, inner_top, inner_right - inner_left, inner_bottom - inner_top))


class RoofTileTexture(ProceduralTexture):
	def __init__(self, seed=7):
		super().__init__(128, 128, 2.0, 2.0)
		self.random = random.Random(seed)
		self.tile_pixel_width = 16
		self.tile_pixel_height = 8
		self.joint_color = (96, 38, 26, 255)
		self.base_color = (196, 88, 56)

	def paint(self, surface):
		surface.fill(self.joint_color)
		rows = self.height // self.tile_pixel_height
		columns = self.width // self.tile_pixel_width
		for row in range(rows):
			shift = (self.tile_pixel_width // 2) * (row % 2)
			for column in range(-1, columns + 1):
				self.paint_tile(surface, column * self.tile_pixel_width + shift, row * self.tile_pixel_height)

	def paint_tile(self, surface, left, top):
		shade = self.random.uniform(0.8, 1.1)
		color = tuple(min(255, int(channel * shade)) for channel in self.base_color)
		darker = tuple(int(channel * 0.72) for channel in color)
		tile = pygame.Rect(left + 1, top, self.tile_pixel_width - 2, self.tile_pixel_height - 1)
		surface.fill(color, tile)
		surface.fill(darker, pygame.Rect(tile.x, tile.bottom - 2, tile.width, 2))


class Material:
	def __init__(self, color, texture=None):
		self.color = color
		self.texture = texture

	def apply(self):
		if self.texture is None:
			glDisable(GL_TEXTURE_2D)
		else:
			glEnable(GL_TEXTURE_2D)
			glBindTexture(GL_TEXTURE_2D, self.texture.texture_id)
		glColor3f(*self.color)

	def texture_coordinates(self, point, tangent, bitangent):
		return point.dot(tangent) / self.texture.span_u, point.dot(bitangent) / self.texture.span_v


class Polygon:
	def __init__(self, points):
		self.points = points
		self.normal = self.compute_normal()

	def compute_normal(self):
		origin = self.points[0]
		for index in range(1, len(self.points) - 1):
			normal = (self.points[index] - origin).cross(self.points[index + 1] - origin)
			if normal.length() > 1e-9:
				return normal.normalized()
		return Vector3.up()

	def surface_axes(self):
		if abs(self.normal.y) > 0.99:
			return Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0)
		tangent = Vector3.up().cross(self.normal).normalized()
		return tangent, self.normal.cross(tangent)

	def triangles(self):
		for index in range(1, len(self.points) - 1):
			yield self.points[0], self.points[index], self.points[index + 1]


class MeshBuilder:
	def __init__(self):
		self.groups = {}

	def polygon(self, material, *points):
		cleaned = []
		for point in points:
			if not cleaned or not cleaned[-1].is_close_to(point):
				cleaned.append(point)
		if len(cleaned) > 1 and cleaned[0].is_close_to(cleaned[-1]):
			cleaned.pop()
		if len(cleaned) >= 3:
			self.groups.setdefault(material, []).append(Polygon(cleaned))

	def oriented_box(self, material, center, axis, normal, half_width, half_depth, bottom, top):
		footprint = [
			center + axis * (-half_width) + normal * (-half_depth),
			center + axis * half_width + normal * (-half_depth),
			center + axis * half_width + normal * half_depth,
			center + axis * (-half_width) + normal * half_depth,
		]
		lower = [corner.at_height(bottom) for corner in footprint]
		upper = [corner.at_height(top) for corner in footprint]
		self.polygon(material, *lower)
		self.polygon(material, *upper)
		for index in range(4):
			following = (index + 1) % 4
			self.polygon(material, lower[index], lower[following], upper[following], upper[index])

	def box(self, material, minimum, maximum):
		center = Vector3((minimum.x + maximum.x) / 2, 0.0, (minimum.z + maximum.z) / 2)
		self.oriented_box(
			material, center, Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0),
			(maximum.x - minimum.x) / 2, (maximum.z - minimum.z) / 2, minimum.y, maximum.y,
		)

	def ring_point(self, center, radius, height, angle):
		return Vector3(center.x + radius * math.cos(angle), height, center.z + radius * math.sin(angle))

	def ring(self, material, center, bottom_radius, top_radius, bottom, top, sides):
		phase = math.pi / sides
		for index in range(sides):
			start = phase + index * 2 * math.pi / sides
			end = phase + (index + 1) * 2 * math.pi / sides
			self.polygon(
				material,
				self.ring_point(center, bottom_radius, bottom, start),
				self.ring_point(center, bottom_radius, bottom, end),
				self.ring_point(center, top_radius, top, end),
				self.ring_point(center, top_radius, top, start),
			)

	def disc(self, material, center, radius, height, sides):
		phase = math.pi / sides
		points = [self.ring_point(center, radius, height, phase + index * 2 * math.pi / sides) for index in range(sides)]
		self.polygon(material, *points)

	def lathe(self, material, center, profile, sides):
		first_radius, first_height = profile[0]
		if first_radius > 0:
			self.disc(material, center, first_radius, first_height, sides)
		for (bottom_radius, bottom), (top_radius, top) in zip(profile, profile[1:]):
			self.ring(material, center, bottom_radius, top_radius, bottom, top, sides)

	def compile(self):
		list_id = glGenLists(1)
		glNewList(list_id, GL_COMPILE)
		for material, polygons in self.groups.items():
			material.apply()
			glBegin(GL_TRIANGLES)
			for polygon in polygons:
				normal = polygon.normal
				glNormal3f(normal.x, normal.y, normal.z)
				tangent, bitangent = polygon.surface_axes()
				for triangle in polygon.triangles():
					for point in triangle:
						if material.texture is not None:
							glTexCoord2f(*material.texture_coordinates(point, tangent, bitangent))
						glVertex3f(point.x, point.y, point.z)
			glEnd()
		glDisable(GL_TEXTURE_2D)
		glEndList()
		return list_id


class TownHallPalette:
	def __init__(self):
		self.sgraffito_texture = SgraffitoTexture().upload()
		self.roof_texture = RoofTileTexture().upload()
		self.plaster = Material((0.94, 0.92, 0.86))
		self.sgraffito = Material((1.0, 1.0, 1.0), self.sgraffito_texture)
		self.roof = Material((1.0, 1.0, 1.0), self.roof_texture)
		self.trim = Material((0.6, 0.59, 0.55))
		self.frame = Material((0.62, 0.12, 0.1))
		self.glass = Material((0.12, 0.12, 0.15))
		self.copper = Material((0.38, 0.62, 0.52))
		self.copper_dark = Material((0.2, 0.37, 0.32))
		self.shadow = Material((0.07, 0.08, 0.09))
		self.wood = Material((0.4, 0.23, 0.12))
		self.clock_face = Material((0.95, 0.95, 0.9))
		self.ink = Material((0.12, 0.12, 0.12))
		self.gold = Material((0.86, 0.7, 0.26))
		self.flag = Material((0.82, 0.1, 0.12))

	def release(self):
		self.sgraffito_texture.release()
		self.roof_texture.release()


class Facade:
	def __init__(self, builder, palette, origin, axis, normal):
		self.builder = builder
		self.palette = palette
		self.origin = origin.at_height(0.0)
		self.axis = axis
		self.normal = normal
		self.up = Vector3.up()

	def point(self, u, v):
		return self.origin + self.axis * u + self.up * v

	def panel(self, material, center, width, height, offset):
		base = center + self.normal * offset
		half_axis = self.axis * (width / 2)
		half_up = self.up * (height / 2)
		self.builder.polygon(
			material, base - half_axis - half_up, base + half_axis - half_up,
			base + half_axis + half_up, base - half_axis + half_up,
		)

	def window(self, u, v, width, height):
		center = self.point(u, v)
		self.panel(self.palette.trim, center, width + 0.36, height + 0.36, 0.03)
		self.panel(self.palette.frame, center, width, height, 0.06)
		pane_width = (width - 0.3) / 2
		pane_height = (height - 0.3) / 2
		for side_x in (-1, 1):
			for side_y in (-1, 1):
				offset = self.axis * (side_x * (pane_width / 2 + 0.05)) + self.up * (side_y * (pane_height / 2 + 0.05))
				self.panel(self.palette.glass, center + offset, pane_width, pane_height, 0.08)

	def window_row(self, count, start, end, v, width, height):
		step = (end - start) / count
		for index in range(count):
			self.window(start + step * (index + 0.5), v, width, height)

	def door(self, u, width, height):
		center = self.point(u, height / 2)
		self.panel(self.palette.trim, center + self.up * 0.15, width + 0.4, height + 0.3, 0.03)
		self.panel(self.palette.wood, center, width, height, 0.06)
		self.panel(self.palette.shadow, center, 0.06, height, 0.08)

	def flag(self, u, top, width, height):
		self.panel(self.palette.flag, self.point(u, top - height / 2), width, height, 0.12)

	def circle(self, material, center, radius, offset, sides=24):
		base = center + self.normal * offset
		points = []
		for index in range(sides):
			angle = index * 2 * math.pi / sides
			points.append(base + (self.axis * math.cos(angle) + self.up * math.sin(angle)) * radius)
		self.builder.polygon(material, *points)

	def hand(self, center, angle, length, width, offset):
		direction = self.axis * math.cos(angle) + self.up * math.sin(angle)
		across = self.axis * (-math.sin(angle)) + self.up * math.cos(angle)
		base = center + self.normal * offset
		self.builder.polygon(
			self.palette.gold, base - across * (width / 2), base + direction * length - across * (width / 4),
			base + direction * length + across * (width / 4), base + across * (width / 2),
		)

	def clock(self, u, v, radius):
		center = self.point(u, v)
		self.circle(self.palette.ink, center, radius + 0.18, 0.04)
		self.circle(self.palette.clock_face, center, radius, 0.07)
		for hour in range(12):
			angle = hour * math.pi / 6
			mark = center + (self.axis * math.cos(angle) + self.up * math.sin(angle)) * (radius * 0.82)
			self.panel(self.palette.ink, mark, 0.12, 0.12, 0.09)
		self.hand(center, math.radians(60), radius * 0.55, 0.16, 0.1)
		self.hand(center, math.radians(150), radius * 0.8, 0.11, 0.11)
		self.circle(self.palette.gold, center, 0.1, 0.12, 8)


class WallSides:
	def __init__(self, x_range, z_range):
		self.x_min, self.x_max = x_range
		self.z_min, self.z_max = z_range

	def side(self, name):
		width = self.x_max - self.x_min
		depth = self.z_max - self.z_min
		east_axis = Vector3(1.0, 0.0, 0.0)
		south_axis = Vector3(0.0, 0.0, 1.0)
		sides = {
			"north": (Vector3(self.x_min, 0.0, self.z_min), east_axis, -south_axis, width),
			"south": (Vector3(self.x_min, 0.0, self.z_max), east_axis, south_axis, width),
			"west": (Vector3(self.x_min, 0.0, self.z_min), south_axis, -east_axis, depth),
			"east": (Vector3(self.x_max, 0.0, self.z_min), south_axis, east_axis, depth),
		}
		return sides[name]

	def all_sides(self):
		return [self.side(name) for name in ("north", "south", "west", "east")]


class SteppedGable:
	def __init__(self, palette, center, axis, normal, half_width, base, top, steps, thickness=0.5, with_windows=True):
		self.palette = palette
		self.center = center.at_height(0.0)
		self.axis = axis
		self.normal = normal
		self.half_width = half_width
		self.base = base
		self.top = top
		self.steps = steps
		self.thickness = thickness
		self.with_windows = with_windows

	def step_half_width(self, index):
		return self.half_width * (1 - index / self.steps)

	def build(self, builder):
		step_height = (self.top - self.base) / self.steps
		half_depth = self.thickness / 2
		for index in range(self.steps):
			half = self.step_half_width(index)
			bottom = self.base + index * step_height
			top = bottom + step_height
			builder.oriented_box(self.palette.plaster, self.center, self.axis, self.normal, half, half_depth, bottom, top)
			builder.oriented_box(self.palette.trim, self.center, self.axis, self.normal, half + 0.12, half_depth + 0.08, top - 0.05, top + 0.12)
			for side in (-1, 1):
				corner = self.center + self.axis * (side * (half - 0.05))
				builder.oriented_box(self.palette.trim, corner, self.axis, self.normal, 0.13, 0.13, top + 0.12, top + 0.62)
				builder.oriented_box(self.palette.copper_dark, corner, self.axis, self.normal, 0.06, 0.06, top + 0.62, top + 0.85)
		finial_height = self.top + 0.12
		builder.oriented_box(self.palette.trim, self.center, self.axis, self.normal, 0.25, 0.2, finial_height, finial_height + 0.9)
		builder.lathe(self.palette.copper, self.center, [(0.18, finial_height + 0.9), (0.2, finial_height + 1.1), (0.0, finial_height + 1.6)], 8)
		if self.with_windows:
			self.build_windows(builder, step_height)

	def build_windows(self, builder, step_height):
		facade = Facade(builder, self.palette, self.center + self.normal * (self.thickness / 2), self.axis, self.normal)
		window_height = min(1.25, step_height * 0.6)
		window_width = window_height * 0.62
		spacing = window_width + 0.55
		for index in range(self.steps - 1):
			available = 2 * self.step_half_width(index + 1) - 0.4
			count = min(3, int(available // spacing))
			v = self.base + (index + 0.5) * step_height
			for slot in range(count):
				facade.window((slot - (count - 1) / 2) * spacing, v, window_width, window_height)


class GabledBlock:
	def __init__(self, palette, x_range, z_range, wall_height, ridge_height, ridge_axis, walls,
			gable_ends=(), gable_steps=5, roof_extension=(0.0, 0.0), window_levels=(2.2, 6.2)):
		self.palette = palette
		self.sides = WallSides(x_range, z_range)
		self.x_range = x_range
		self.z_range = z_range
		self.wall_height = wall_height
		self.ridge_height = ridge_height
		self.ridge_axis = ridge_axis
		self.walls = walls
		self.gable_ends = gable_ends
		self.gable_steps = gable_steps
		self.roof_extension = roof_extension
		self.window_levels = window_levels
		self.eave_overhang = 0.4
		self.verge_overhang = 0.25

	def build(self, builder):
		for side_name, (window_count, start, end) in self.walls.items():
			origin, axis, normal, length = self.sides.side(side_name)
			self.build_wall(builder, origin, axis, normal, length, window_count, start, end)
		self.build_roof(builder)
		for side_name in self.gable_ends:
			self.build_gable(builder, side_name)

	def build_wall(self, builder, origin, axis, normal, length, window_count, start, end):
		up = Vector3.up()
		builder.polygon(
			self.palette.plaster, origin, origin + axis * length,
			origin + axis * length + up * self.wall_height, origin + up * self.wall_height,
		)
		middle = origin + axis * (length / 2)
		builder.oriented_box(self.palette.trim, middle + normal * 0.08, axis, normal, length / 2 + 0.08, 0.1, self.wall_height - 0.65, self.wall_height - 0.35)
		builder.oriented_box(self.palette.trim, middle + normal * 0.04, axis, normal, length / 2 + 0.04, 0.06, 0.0, 0.7)
		if window_count:
			facade = Facade(builder, self.palette, origin, axis, normal)
			for level in self.window_levels:
				facade.window_row(window_count, start, end, level, 1.1, 1.8)

	def ridge_layout(self):
		if self.ridge_axis == "x":
			return self.x_range, self.z_range, Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0)
		return self.z_range, self.x_range, Vector3(0.0, 0.0, 1.0), Vector3(1.0, 0.0, 0.0)

	def build_roof(self, builder):
		(along_min, along_max), (across_min, across_max), along, across = self.ridge_layout()
		half_span = (across_max - across_min) / 2
		ridge_offset = (across_min + across_max) / 2
		slope = (self.ridge_height - self.wall_height) / half_span
		eave_height = self.wall_height - self.eave_overhang * slope
		start = along_min - self.verge_overhang - self.roof_extension[0]
		end = along_max + self.verge_overhang + self.roof_extension[1]
		up = Vector3.up()
		ridge_start = along * start + across * ridge_offset + up * self.ridge_height
		ridge_end = along * end + across * ridge_offset + up * self.ridge_height
		for eave_offset in (across_max + self.eave_overhang, across_min - self.eave_overhang):
			eave_start = along * start + across * eave_offset + up * eave_height
			eave_end = along * end + across * eave_offset + up * eave_height
			builder.polygon(self.palette.roof, eave_start, eave_end, ridge_end, ridge_start)
		builder.oriented_box(
			self.palette.roof, along * ((start + end) / 2) + across * ridge_offset, along, across,
			(end - start) / 2, 0.14, self.ridge_height - 0.1, self.ridge_height + 0.12,
		)

	def build_gable(self, builder, side_name):
		origin, axis, normal, length = self.sides.side(side_name)
		center = origin + axis * (length / 2)
		SteppedGable(
			self.palette, center, axis, normal, length / 2, self.wall_height, self.ridge_height, self.gable_steps,
		).build(builder)


class Dormer:
	def __init__(self, palette, center_x, front_z, back_z, half_width, base, body_top, gable_top):
		self.palette = palette
		self.center_x = center_x
		self.front_z = front_z
		self.back_z = back_z
		self.half_width = half_width
		self.base = base
		self.body_top = body_top
		self.gable_top = gable_top

	def build(self, builder):
		left = self.center_x - self.half_width
		right = self.center_x + self.half_width
		builder.box(self.palette.plaster, Vector3(left, self.base, self.back_z), Vector3(right, self.body_top, self.front_z))
		builder.box(
			self.palette.trim, Vector3(left - 0.12, self.body_top - 0.12, self.front_z - 0.3),
			Vector3(right + 0.12, self.body_top + 0.08, self.front_z + 0.14),
		)
		facade = Facade(builder, self.palette, Vector3(self.center_x, 0.0, self.front_z), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0))
		for u in (-0.85, 0.85):
			facade.window(u, (self.base + self.body_top) / 2 + 0.25, 0.7, 1.15)
		SteppedGable(
			self.palette, Vector3(self.center_x, 0.0, self.front_z - 0.2), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0),
			self.half_width, self.body_top, self.gable_top, 4, thickness=0.4,
		).build(builder)
		ridge = self.gable_top - 0.35
		roof_front = self.front_z - 0.3
		for side in (left - 0.15, right + 0.15):
			builder.polygon(
				self.palette.roof,
				Vector3(side, self.body_top - 0.1, self.back_z), Vector3(side, self.body_top - 0.1, roof_front),
				Vector3(self.center_x, ridge, roof_front), Vector3(self.center_x, ridge, self.back_z),
			)


class Lantern:
	def __init__(self, palette, center, radius, bottom, top, sides=8):
		self.palette = palette
		self.center = center.at_height(0.0)
		self.radius = radius
		self.bottom = bottom
		self.top = top
		self.sides = sides

	def build(self, builder):
		builder.ring(self.palette.shadow, self.center, self.radius * 0.6, self.radius * 0.6, self.bottom, self.top, self.sides)
		builder.lathe(self.palette.copper_dark, self.center, [(self.radius + 0.1, self.bottom), (self.radius + 0.1, self.bottom + 0.15)], self.sides)
		post_size = max(0.07, self.radius * 0.1)
		phase = math.pi / self.sides
		for index in range(self.sides):
			angle = phase + index * 2 * math.pi / self.sides
			radial = Vector3(math.cos(angle), 0.0, math.sin(angle))
			tangent = Vector3(-math.sin(angle), 0.0, math.cos(angle))
			builder.oriented_box(
				self.palette.copper, self.center + radial * self.radius, tangent, radial,
				post_size, post_size, self.bottom + 0.15, self.top,
			)
		builder.lathe(self.palette.copper_dark, self.center, [(self.radius + 0.12, self.top), (self.radius + 0.12, self.top + 0.12)], self.sides)


class CornerTower:
	def __init__(self, palette, center, half_size, shaft_height):
		self.palette = palette
		self.center = center.at_height(0.0)
		self.half_size = half_size
		self.shaft_height = shaft_height

	def build(self, builder):
		x_range = (self.center.x - self.half_size, self.center.x + self.half_size)
		z_range = (self.center.z - self.half_size, self.center.z + self.half_size)
		builder.box(self.palette.sgraffito, Vector3(x_range[0], 0.0, z_range[0]), Vector3(x_range[1], self.shaft_height, z_range[1]))
		builder.box(self.palette.trim, Vector3(x_range[0] - 0.05, 0.0, z_range[0] - 0.05), Vector3(x_range[1] + 0.05, 0.5, z_range[1] + 0.05))
		for origin, axis, normal, length in WallSides(x_range, z_range).all_sides():
			facade = Facade(builder, self.palette, origin, axis, normal)
			for level in (2.4, 5.2, 8.0):
				facade.window_row(2, 0.6, length - 0.6, level, 0.75, 1.4)
		cornice_top = self.shaft_height + 0.4
		cornice_half = self.half_size + 0.18
		builder.box(
			self.palette.trim, Vector3(self.center.x - cornice_half, self.shaft_height, self.center.z - cornice_half),
			Vector3(self.center.x + cornice_half, cornice_top, self.center.z + cornice_half),
		)
		self.build_skirt(builder, cornice_half + 0.1, cornice_top)
		self.build_drum(builder, cornice_top)
		self.build_helmet(builder, cornice_top + 2.7)

	def build_skirt(self, builder, half, bottom):
		inner = 1.9
		top = bottom + 0.9
		corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
		for index in range(4):
			sx0, sz0 = corners[index]
			sx1, sz1 = corners[(index + 1) % 4]
			builder.polygon(
				self.palette.roof,
				Vector3(self.center.x + sx0 * half, bottom, self.center.z + sz0 * half),
				Vector3(self.center.x + sx1 * half, bottom, self.center.z + sz1 * half),
				Vector3(self.center.x + sx1 * inner, top, self.center.z + sz1 * inner),
				Vector3(self.center.x + sx0 * inner, top, self.center.z + sz0 * inner),
			)

	def build_drum(self, builder, bottom):
		radius = 2.05
		top = bottom + 2.7
		builder.ring(self.palette.plaster, self.center, radius, radius, bottom, top, 8)
		apothem = radius * math.cos(math.pi / 8)
		for angle in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
			normal = Vector3(math.cos(angle), 0.0, math.sin(angle))
			axis = Vector3(-math.sin(angle), 0.0, math.cos(angle))
			Facade(builder, self.palette, self.center + normal * apothem, axis, normal).window(0.0, bottom + 1.55, 0.6, 1.0)
		builder.lathe(self.palette.trim, self.center, [(radius + 0.15, top - 0.1), (radius + 0.15, top + 0.2)], 8)

	def build_helmet(self, builder, base):
		builder.lathe(self.palette.copper, self.center, [
			(2.25, base + 0.2), (2.12, base + 0.75), (1.78, base + 1.35), (1.22, base + 1.85), (0.78, base + 2.1),
		], 8)
		lantern_top = base + 3.45
		Lantern(self.palette, self.center, 0.75, base + 2.1, lantern_top).build(builder)
		builder.lathe(self.palette.copper, self.center, [
			(0.88, lantern_top + 0.12), (1.0, lantern_top + 0.45), (0.86, lantern_top + 0.95), (0.46, lantern_top + 1.4),
			(0.15, lantern_top + 1.75), (0.12, lantern_top + 2.1), (0.26, lantern_top + 2.3), (0.12, lantern_top + 2.5),
			(0.0, lantern_top + 5.0),
		], 8)


class ClockTower:
	def __init__(self, palette, center, half_size, shaft_height):
		self.palette = palette
		self.center = center.at_height(0.0)
		self.half_size = half_size
		self.shaft_height = shaft_height

	def build(self, builder):
		x_range = (self.center.x - self.half_size, self.center.x + self.half_size)
		z_range = (self.center.z - self.half_size, self.center.z + self.half_size)
		builder.box(self.palette.sgraffito, Vector3(x_range[0], 0.0, z_range[0]), Vector3(x_range[1], self.shaft_height, z_range[1]))
		for origin, axis, normal, length in WallSides(x_range, z_range).all_sides():
			facade = Facade(builder, self.palette, origin, axis, normal)
			for level in (4.0, 9.0, 13.5, 17.5):
				facade.window(length / 2, level, 0.7, 1.4)
			facade.clock(length / 2, self.shaft_height - 3.0, 1.1)
		cornice_half = self.half_size + 0.3
		cornice_top = self.shaft_height + 0.45
		builder.box(
			self.palette.trim, Vector3(self.center.x - cornice_half, self.shaft_height, self.center.z - cornice_half),
			Vector3(self.center.x + cornice_half, cornice_top, self.center.z + cornice_half),
		)
		self.build_balustrade(builder, cornice_half - 0.12, cornice_top)
		self.build_helmet(builder, cornice_top)

	def build_balustrade(self, builder, half, bottom):
		top = bottom + 0.95
		east = Vector3(1.0, 0.0, 0.0)
		south = Vector3(0.0, 0.0, 1.0)
		edges = [
			(self.center + south * (-half), east, south),
			(self.center + south * half, east, south),
			(self.center + east * (-half), south, east),
			(self.center + east * half, south, east),
		]
		posts = 11
		for middle, axis, normal in edges:
			builder.oriented_box(self.palette.trim, middle, axis, normal, half + 0.1, 0.12, top, top + 0.16)
			for index in range(posts + 1):
				offset = -half + index * 2 * half / posts
				builder.oriented_box(self.palette.trim, middle + axis * offset, axis, normal, 0.06, 0.06, bottom, top)

	def build_helmet(self, builder, base):
		builder.lathe(self.palette.copper, self.center, [
			(2.3, base), (2.15, base + 0.95), (1.8, base + 1.9), (1.42, base + 2.5), (1.32, base + 2.7),
		], 8)
		first_lantern_top = base + 5.0
		Lantern(self.palette, self.center, 1.32, base + 2.7, first_lantern_top).build(builder)
		builder.lathe(self.palette.copper, self.center, [
			(1.5, first_lantern_top + 0.12), (1.5, first_lantern_top + 0.35), (1.22, first_lantern_top + 1.05),
			(0.82, first_lantern_top + 1.65), (0.62, first_lantern_top + 1.9),
		], 8)
		second_lantern_top = first_lantern_top + 3.1
		Lantern(self.palette, self.center, 0.62, first_lantern_top + 1.9, second_lantern_top).build(builder)
		builder.lathe(self.palette.copper, self.center, [
			(0.76, second_lantern_top + 0.12), (0.84, second_lantern_top + 0.45), (0.64, second_lantern_top + 1.05),
			(0.27, second_lantern_top + 1.55), (0.15, second_lantern_top + 2.15), (0.3, second_lantern_top + 2.45),
			(0.14, second_lantern_top + 2.75), (0.0, second_lantern_top + 6.5),
		], 8)
		builder.lathe(self.palette.gold, self.center, [
			(0.0, second_lantern_top + 4.0), (0.22, second_lantern_top + 4.2), (0.0, second_lantern_top + 4.4),
		], 8)


class Arcade:
	def __init__(self, palette, x_range, back_z, front_z, bays, wall_height):
		self.palette = palette
		self.x_min, self.x_max = x_range
		self.back_z = back_z
		self.front_z = front_z
		self.bays = bays
		self.wall_height = wall_height
		self.bay_width = (self.x_max - self.x_min) / bays
		self.spring_height = 2.75
		self.ground_floor_top = 4.6
		self.gallery_floor_top = 5.0
		self.beam_bottom = 8.4

	def bay_center(self, index):
		return self.x_min + self.bay_width * (index + 0.5)

	def pier_x(self, index):
		return self.x_min + self.bay_width * index

	def build(self, builder):
		self.build_back_wall(builder)
		self.build_arches(builder)
		self.build_columns(builder)
		self.build_gallery(builder)

	def build_back_wall(self, builder):
		origin = Vector3(self.x_min, 0.0, self.back_z)
		axis = Vector3(1.0, 0.0, 0.0)
		up = Vector3.up()
		length = self.x_max - self.x_min
		builder.polygon(self.palette.plaster, origin, origin + axis * length, origin + axis * length + up * self.wall_height, origin + up * self.wall_height)
		facade = Facade(builder, self.palette, origin, axis, Vector3(0.0, 0.0, 1.0))
		for index in range(self.bays):
			u = self.bay_width * (index + 0.5)
			if index % 2 == 1:
				facade.door(u, 1.4, 2.7)
			else:
				facade.window(u, 2.0, 1.1, 1.6)
			facade.window(u, 6.8, 1.1, 1.8)

	def build_arches(self, builder):
		radius = self.bay_width / 2 - 0.25
		depth_back = self.front_z - 0.4
		segments = 12
		for index in range(self.bays):
			center_x = self.bay_center(index)
			for segment in range(segments):
				start = math.pi - segment * math.pi / segments
				end = math.pi - (segment + 1) * math.pi / segments
				x0 = center_x + radius * math.cos(start)
				y0 = self.spring_height + radius * math.sin(start)
				x1 = center_x + radius * math.cos(end)
				y1 = self.spring_height + radius * math.sin(end)
				for z in (self.front_z, depth_back):
					builder.polygon(
						self.palette.plaster, Vector3(x0, y0, z), Vector3(x1, y1, z),
						Vector3(x1, self.ground_floor_top, z), Vector3(x0, self.ground_floor_top, z),
					)
				builder.polygon(
					self.palette.plaster, Vector3(x0, y0, self.front_z), Vector3(x1, y1, self.front_z),
					Vector3(x1, y1, depth_back), Vector3(x0, y0, depth_back),
				)
		for index in range(self.bays + 1):
			x = self.pier_x(index)
			builder.box(self.palette.plaster, Vector3(x - 0.25, self.spring_height - 0.15, depth_back), Vector3(x + 0.25, self.ground_floor_top, self.front_z))
			builder.box(self.palette.trim, Vector3(x - 0.32, self.spring_height - 0.3, depth_back - 0.05), Vector3(x + 0.32, self.spring_height - 0.1, self.front_z + 0.05))

	def build_columns(self, builder):
		column_z = self.front_z - 0.2
		for index in range(1, self.bays):
			center = Vector3(self.pier_x(index), 0.0, column_z)
			builder.box(self.palette.trim, Vector3(center.x - 0.3, 0.0, column_z - 0.3), Vector3(center.x + 0.3, 0.35, column_z + 0.3))
			builder.ring(self.palette.trim, center, 0.22, 0.2, 0.35, self.spring_height - 0.3, 10)
			builder.ring(self.palette.trim, center, 0.17, 0.15, self.gallery_floor_top, self.beam_bottom, 10)

	def build_gallery(self, builder):
		rail_back = self.front_z - 0.3
		rail_front = self.front_z
		builder.box(self.palette.trim, Vector3(self.x_min, self.ground_floor_top, self.back_z), Vector3(self.x_max, self.gallery_floor_top, self.front_z + 0.15))
		builder.box(self.palette.trim, Vector3(self.x_min, self.gallery_floor_top, rail_back), Vector3(self.x_max, self.gallery_floor_top + 0.15, rail_front))
		rail_top = self.gallery_floor_top + 1.0
		builder.box(self.palette.trim, Vector3(self.x_min, rail_top - 0.18, rail_back), Vector3(self.x_max, rail_top, rail_front + 0.05))
		baluster_x = self.x_min + 0.2
		while baluster_x < self.x_max - 0.1:
			builder.box(
				self.palette.trim, Vector3(baluster_x - 0.05, self.gallery_floor_top + 0.15, rail_back + 0.1),
				Vector3(baluster_x + 0.05, rail_top - 0.18, rail_front - 0.1),
			)
			baluster_x += 0.3
		facade = Facade(builder, self.palette, Vector3(self.x_min, 0.0, rail_front), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0))
		for index in range(1, self.bays):
			facade.flag(self.bay_width * index + 0.45, rail_top + 0.3, 0.32, 1.25)
		builder.box(self.palette.plaster, Vector3(self.x_min, self.beam_bottom, self.front_z - 0.6), Vector3(self.x_max, self.wall_height - 0.2, self.front_z + 0.1))
		builder.box(self.palette.trim, Vector3(self.x_min, self.beam_bottom - 0.12, self.front_z - 0.62), Vector3(self.x_max, self.beam_bottom + 0.05, self.front_z + 0.2))
		builder.polygon(
			self.palette.plaster, Vector3(self.x_min, self.beam_bottom, self.back_z), Vector3(self.x_max, self.beam_bottom, self.back_z),
			Vector3(self.x_max, self.beam_bottom, self.front_z - 0.6), Vector3(self.x_min, self.beam_bottom, self.front_z - 0.6),
		)


class TownHall:
	def __init__(self):
		self.palette = TownHallPalette()
		self.center = Vector3(0.0, 0.0, -9.0)
		self.height = 40.0
		self.parts = self.create_parts()
		builder = MeshBuilder()
		for part in self.parts:
			part.build(builder)
		self.display_list = builder.compile()

	def create_parts(self):
		palette = self.palette
		wall_height = 9.0
		parts = [
			GabledBlock(
				palette, (-13.0, 13.0), (-4.0, 6.0), wall_height, 17.0, "x",
				walls={"north": (6, 0.8, 25.2), "west": (1, 0.5, 5.5), "east": (1, 0.5, 5.5)},
				gable_ends=("west", "east"), gable_steps=6,
			),
			GabledBlock(
				palette, (-13.0, -5.0), (-20.0, -4.0), wall_height, 16.0, "z",
				walls={"west": (6, 0.8, 15.2), "east": (6, 0.8, 15.2), "north": (3, 0.8, 7.2)},
				gable_ends=("north",), roof_extension=(0.0, 5.0),
			),
			GabledBlock(
				palette, (5.0, 13.0), (-20.0, -4.0), wall_height, 16.0, "z",
				walls={"west": (6, 0.8, 15.2), "east": (6, 0.8, 15.2), "north": (3, 0.8, 7.2)},
				gable_ends=("north",), roof_extension=(0.0, 5.0),
			),
			GabledBlock(
				palette, (-5.0, 5.0), (-20.0, -14.0), 8.0, 13.0, "x",
				walls={"north": (4, 0.6, 9.4), "south": (4, 0.6, 9.4)},
				roof_extension=(3.0, 3.0), window_levels=(2.0, 5.6),
			),
			Arcade(palette, (-9.5, 9.5), 3.0, 6.0, 5, wall_height),
			CornerTower(palette, Vector3(-12.0, 0.0, 5.0), 2.5, 9.6),
			CornerTower(palette, Vector3(12.0, 0.0, 5.0), 2.5, 9.6),
			ClockTower(palette, Vector3(0.0, 0.0, -22.5), 2.5, 24.0),
		]
		for center_x in (-5.4, 0.0, 5.4):
			parts.append(Dormer(palette, center_x, 4.6, 1.5, 1.9, 10.2, 12.3, 16.0))
		return parts

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_TEXTURE_BIT)
		glEnable(GL_LIGHTING)
		glEnable(GL_NORMALIZE)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
		glCallList(self.display_list)
		glPopAttrib()

	def release(self):
		glDeleteLists(self.display_list, 1)
		self.palette.release()
