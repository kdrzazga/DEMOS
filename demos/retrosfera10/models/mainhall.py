import math
import os
import random

import pygame
from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GL_ENABLE_BIT, GL_FRONT_AND_BACK, GL_LIGHTING, GL_LIGHTING_BIT,
	GL_LIGHT_MODEL_TWO_SIDE, GL_NORMALIZE, GL_TEXTURE_BIT, GL_TRUE, glCallList, glColorMaterial, glDeleteLists,
	glEnable, glLightModeli, glPopAttrib, glPopMatrix, glPushAttrib, glPushMatrix, glScalef, glTranslatef,
)

from lib.big_screen import BigScreen
from demos.retrosfera10.models.doll import Doll, DollLook
from demos.retrosfera10.models.townhall import Facade, Material, MeshBuilder, ProceduralTexture, Vector3


class ParquetTexture(ProceduralTexture):
	def __init__(self, panel_span=2.0, seed=3):
		super().__init__(256, 256, panel_span, panel_span)
		self.random = random.Random(seed)
		self.strip_color = (168, 122, 72)
		self.tile_color = (228, 190, 132)
		self.joint_color = (150, 108, 62)
		self.knot_color = (196, 150, 94)
		self.strip_pixels = 22
		self.joint_pixels = 3

	def shade(self, color, low, high):
		factor = self.random.uniform(low, high)
		return tuple(min(255, int(channel * factor)) for channel in color)

	def paint(self, surface):
		surface.fill(self.strip_color)
		self.paint_strip_grain(surface)
		half_strip = self.strip_pixels // 2
		inner = self.width - self.strip_pixels
		tile = (inner - self.joint_pixels) // 2
		for row in range(2):
			for column in range(2):
				left = half_strip + column * (tile + self.joint_pixels)
				top = half_strip + row * (tile + self.joint_pixels)
				surface.fill(self.shade(self.tile_color, 0.93, 1.05), pygame.Rect(left, top, tile, tile))
		surface.fill(self.joint_color, pygame.Rect(half_strip, half_strip + tile, inner, self.joint_pixels))
		surface.fill(self.joint_color, pygame.Rect(half_strip + tile, half_strip, self.joint_pixels, inner))
		for corner_x in (0, self.width):
			for corner_y in (0, self.height):
				self.paint_knot(surface, corner_x, corner_y)

	def paint_strip_grain(self, surface):
		for _ in range(160):
			color = self.shade(self.strip_color, 0.82, 1.08)
			offset = self.random.randrange(self.width)
			position = self.random.randrange(-self.strip_pixels // 2, self.strip_pixels // 2)
			length = self.random.randrange(20, 90)
			pygame.draw.line(surface, color, (offset, position % self.height), (offset + length, position % self.height))
			pygame.draw.line(surface, color, (position % self.width, offset), (position % self.width, offset + length))

	def paint_knot(self, surface, center_x, center_y):
		reach = self.strip_pixels
		pygame.draw.polygon(surface, self.knot_color, [
			(center_x, center_y - reach), (center_x + reach, center_y), (center_x, center_y + reach), (center_x - reach, center_y),
		])


class DarkWoodTexture(ProceduralTexture):
	def __init__(self, span_u=4.0, span_v=1.0, seed=5):
		super().__init__(256, 64, span_u, span_v)
		self.random = random.Random(seed)
		self.base_color = (78, 49, 29)

	def paint(self, surface):
		surface.fill(self.base_color)
		for row in range(self.height):
			factor = self.random.uniform(0.75, 1.15)
			color = tuple(min(255, int(channel * factor)) for channel in self.base_color)
			start = self.random.randrange(self.width)
			length = self.random.randrange(60, self.width)
			pygame.draw.line(surface, color, (start, row), (start + length, row))
			pygame.draw.line(surface, color, (start - self.width, row), (start + length - self.width, row))


class LeadedGlassTexture(ProceduralTexture):
	def __init__(self, span=0.32):
		super().__init__(64, 64, span, span)
		self.glass_color = (214, 230, 240)
		self.lead_color = (64, 68, 74)

	def paint(self, surface):
		surface.fill(self.glass_color)
		pygame.draw.line(surface, self.lead_color, (0, 0), (self.width, self.height), 3)
		pygame.draw.line(surface, self.lead_color, (0, self.height), (self.width, 0), 3)


class MainHallPalette:
	def __init__(self):
		self.parquet_texture = ParquetTexture().upload()
		self.dark_wood_texture = DarkWoodTexture().upload()
		self.glass_texture = LeadedGlassTexture().upload()
		self.plaster = Material((0.95, 0.95, 0.93))
		self.parquet = Material((1.0, 1.0, 1.0), self.parquet_texture)
		self.dark_wood = Material((1.0, 1.0, 1.0), self.dark_wood_texture)
		self.beam_wood = Material((0.85, 0.85, 0.85), self.dark_wood_texture)
		self.stage_wood = Material((0.8, 0.62, 0.4))
		self.step_edge = Material((0.62, 0.44, 0.26))
		self.furniture_wood = Material((0.46, 0.29, 0.15))
		self.trim = Material((0.36, 0.22, 0.12))
		self.frame = Material((0.42, 0.26, 0.14))
		self.glass = Material((1.0, 1.0, 1.0), self.glass_texture, lit=False)
		self.shadow = Material((0.16, 0.11, 0.07))
		self.brass = Material((0.8, 0.64, 0.3))
		self.dark_brass = Material((0.55, 0.42, 0.2))
		self.iron = Material((0.2, 0.18, 0.15))
		self.candle = Material((0.96, 0.94, 0.86), lit=False)
		self.flame = Material((1.0, 0.86, 0.45), lit=False)

	def release(self):
		self.parquet_texture.release()
		self.dark_wood_texture.release()
		self.glass_texture.release()


class Candle:
	def __init__(self, palette, center, bottom, height=0.2, radius=0.03):
		self.palette = palette
		self.center = center.at_height(0.0)
		self.bottom = bottom
		self.height = height
		self.radius = radius

	def build(self, builder):
		top = self.bottom + self.height
		builder.ring(self.palette.brass, self.center, self.radius * 1.9, self.radius * 1.9, self.bottom - 0.04, self.bottom, 8)
		builder.ring(self.palette.candle, self.center, self.radius, self.radius, self.bottom, top, 8)
		builder.disc(self.palette.candle, self.center, self.radius, top, 8)
		builder.lathe(self.palette.flame, self.center, [
			(0.0, top), (self.radius * 1.1, top + 0.04), (self.radius * 0.8, top + 0.08), (0.0, top + 0.13),
		], 6)


class Chandelier:
	def __init__(self, palette, x, z, ceiling_height, body_height, tiers=((0.8, 0.0, 8), (0.5, 0.5, 6))):
		self.palette = palette
		self.center = Vector3(x, 0.0, z)
		self.ceiling_height = ceiling_height
		self.body_height = body_height
		self.tiers = tiers

	def build(self, builder):
		east = Vector3(1.0, 0.0, 0.0)
		south = Vector3(0.0, 0.0, 1.0)
		body = self.body_height
		builder.oriented_box(self.palette.iron, self.center, east, south, 0.025, 0.025, body + 0.9, self.ceiling_height)
		builder.lathe(self.palette.dark_brass, self.center, [
			(0.03, body - 0.5), (0.1, body - 0.35), (0.17, body - 0.12), (0.12, body), (0.07, body + 0.2),
			(0.13, body + 0.45), (0.06, body + 0.65), (0.09, body + 0.8), (0.03, body + 0.95),
		], 8)
		for radius, lift, count in self.tiers:
			self.build_tier(builder, radius, body + lift, count)

	def build_tier(self, builder, radius, height, count):
		for index in range(count):
			angle = math.tau * index / count + radius
			radial = Vector3(math.cos(angle), 0.0, math.sin(angle))
			tangent = Vector3(-math.sin(angle), 0.0, math.cos(angle))
			builder.oriented_box(self.palette.iron, self.center + radial * (radius / 2), radial, tangent, radius / 2, 0.02, height, height + 0.04)
			tip = self.center + radial * radius
			builder.oriented_box(self.palette.iron, tip, radial, tangent, 0.02, 0.02, height, height + 0.12)
			Candle(self.palette, tip, height + 0.16).build(builder)


class Sconce:
	def __init__(self, palette, facade, u, v):
		self.palette = palette
		self.facade = facade
		self.u = u
		self.v = v

	def build(self, builder):
		center = self.facade.point(self.u, self.v)
		self.facade.circle(self.palette.brass, center, 0.32, 0.02)
		self.facade.circle(self.palette.dark_brass, center + Vector3.up() * 0.04, 0.2, 0.035)
		arm_height = self.v - 0.32
		wall_foot = self.facade.point(self.u, 0.0)
		axis = self.facade.axis
		normal = self.facade.normal
		builder.oriented_box(self.palette.iron, wall_foot + normal * 0.17, axis, normal, 0.03, 0.17, arm_height, arm_height + 0.05)
		builder.oriented_box(self.palette.iron, wall_foot + normal * 0.34, axis, normal, 0.17, 0.03, arm_height, arm_height + 0.05)
		for side in (-1, 1):
			Candle(self.palette, wall_foot + normal * 0.34 + axis * (side * 0.14), arm_height + 0.09).build(builder)


class RadiatorCover:
	def __init__(self, palette, facade, u, width=1.8, height=1.4, depth=0.34, balusters=13):
		self.palette = palette
		self.facade = facade
		self.u = u
		self.width = width
		self.height = height
		self.depth = depth
		self.balusters = balusters

	def build(self, builder):
		axis = self.facade.axis
		normal = self.facade.normal
		foot = self.facade.point(self.u, 0.0)
		half = self.width / 2
		self.facade.panel(self.palette.shadow, self.facade.point(self.u, self.height / 2), self.width, self.height, 0.02)
		builder.oriented_box(self.palette.furniture_wood, foot + normal * (self.depth / 2), axis, normal, half + 0.06, self.depth / 2 + 0.04, self.height - 0.1, self.height)
		builder.oriented_box(self.palette.furniture_wood, foot + normal * (self.depth / 2), axis, normal, half, self.depth / 2, 0.1, 0.22)
		for side in (-1, 1):
			builder.oriented_box(self.palette.furniture_wood, foot + normal * (self.depth / 2) + axis * (side * (half - 0.06)), axis, normal, 0.06, self.depth / 2, 0.1, self.height - 0.1)
		spacing = (self.width - 0.3) / (self.balusters - 1)
		for index in range(self.balusters):
			offset = -half + 0.15 + index * spacing
			builder.ring(self.palette.furniture_wood, foot + normal * (self.depth - 0.06) + axis * offset, 0.035, 0.045, 0.22, self.height - 0.1, 6)


class WindowedWall:
	def __init__(self, palette, origin, axis, normal, length, height, window_centers, opening_width=1.9,
			opening_bottom=1.5, opening_top=4.4, recess=0.5):
		self.palette = palette
		self.origin = origin
		self.axis = axis
		self.normal = normal
		self.length = length
		self.height = height
		self.window_centers = window_centers
		self.opening_width = opening_width
		self.opening_bottom = opening_bottom
		self.opening_top = opening_top
		self.recess = recess

	def facade(self, builder):
		return Facade(builder, self.palette, self.origin, self.axis, self.normal)

	def wall_point(self, u, v):
		return self.origin + self.axis * u + Vector3.up() * v

	def wall_quad(self, builder, u0, u1, v0, v1):
		builder.polygon(self.palette.plaster, self.wall_point(u0, v0), self.wall_point(u1, v0), self.wall_point(u1, v1), self.wall_point(u0, v1))

	def build(self, builder):
		self.wall_quad(builder, 0.0, self.length, 0.0, self.opening_bottom)
		self.wall_quad(builder, 0.0, self.length, self.opening_top, self.height)
		edges = [0.0]
		for center in self.window_centers:
			edges.extend((center - self.opening_width / 2, center + self.opening_width / 2))
		edges.append(self.length)
		for left, right in zip(edges[0::2], edges[1::2]):
			self.wall_quad(builder, left, right, self.opening_bottom, self.opening_top)
		for center in self.window_centers:
			self.build_recess(builder, center)
		facade = self.facade(builder)
		middle = self.origin + self.axis * (self.length / 2)
		builder.oriented_box(self.palette.furniture_wood, middle + self.normal * 0.03, self.axis, self.normal, self.length / 2, 0.03, 0.0, 0.15)
		for center in self.window_centers:
			RadiatorCover(self.palette, facade, center).build(builder)
		for left, right in zip(self.window_centers, self.window_centers[1:]):
			Sconce(self.palette, facade, (left + right) / 2, 3.3).build(builder)

	def build_recess(self, builder, center):
		outward = -self.normal * self.recess
		left = center - self.opening_width / 2
		right = center + self.opening_width / 2
		bottom = self.opening_bottom
		top = self.opening_top
		for u in (left, right):
			builder.polygon(self.palette.plaster, self.wall_point(u, bottom), self.wall_point(u, top), self.wall_point(u, top) + outward, self.wall_point(u, bottom) + outward)
		for v in (bottom, top):
			builder.polygon(self.palette.plaster, self.wall_point(left, v), self.wall_point(right, v), self.wall_point(right, v) + outward, self.wall_point(left, v) + outward)
		back = Facade(builder, self.palette, self.origin + outward, self.axis, self.normal)
		middle = (bottom + top) / 2
		back.panel(self.palette.plaster, back.point(center, middle), self.opening_width, top - bottom, 0.0)
		back.window(center, middle, self.opening_width - 0.6, top - bottom - 0.6)


class Stage:
	def __init__(self, palette, left_x, right_x, back_z, depth=4.0, steps=3, rise=0.17, tread=0.4):
		self.palette = palette
		self.left_x = left_x
		self.right_x = right_x
		self.back_z = back_z
		self.depth = depth
		self.steps = steps
		self.rise = rise
		self.tread = tread

	def front_z(self):
		return self.back_z + self.depth

	def top(self):
		return self.rise * self.steps

	def build(self, builder):
		for index in range(self.steps):
			height = self.rise * (self.steps - index)
			front = self.front_z() + self.tread * index
			builder.box(self.palette.stage_wood, Vector3(self.left_x, 0.0, self.back_z), Vector3(self.right_x, height, front))
			builder.box(self.palette.step_edge, Vector3(self.left_x, height - 0.04, front - 0.06), Vector3(self.right_x, height + 0.01, front + 0.02))


class Ceiling:
	def __init__(self, palette, half_width, half_length, height, joist_spacing=0.75, girder_positions=(-10.0, 0.0, 10.0)):
		self.palette = palette
		self.half_width = half_width
		self.half_length = half_length
		self.height = height
		self.joist_spacing = joist_spacing
		self.girder_positions = girder_positions
		self.joist_depth = 0.32
		self.girder_depth = 0.55

	def underside(self):
		return self.height - self.joist_depth

	def build(self, builder):
		east = Vector3(1.0, 0.0, 0.0)
		south = Vector3(0.0, 0.0, 1.0)
		builder.polygon(
			self.palette.dark_wood,
			Vector3(-self.half_width, self.height, -self.half_length), Vector3(self.half_width, self.height, -self.half_length),
			Vector3(self.half_width, self.height, self.half_length), Vector3(-self.half_width, self.height, self.half_length),
		)
		count = int(2 * self.half_length / self.joist_spacing)
		for index in range(count):
			z = -self.half_length + self.joist_spacing * (index + 0.5)
			builder.oriented_box(self.palette.dark_wood, Vector3(0.0, 0.0, z), east, south, self.half_width, 0.11, self.underside(), self.height)
		girder_bottom = self.underside() - self.girder_depth
		builder.oriented_box(self.palette.beam_wood, Vector3(0.0, 0.0, 0.0), south, east, self.half_length, 0.3, girder_bottom, self.underside())
		for z in self.girder_positions:
			builder.oriented_box(self.palette.beam_wood, Vector3(0.0, 0.0, z), east, south, self.half_width, 0.28, girder_bottom, self.underside())


class StagePerformer:
	def __init__(self, look, stage_side, waving_arm):
		self.look = look
		self.stage_side = stage_side
		self.waving_arm = waving_arm


class MainHall:
	def __init__(self, half_width=8.0, half_length=20.0, height=6.5, windows_per_side=6, chandelier_rows=(-3.6, 3.6),
			chandelier_positions=(-14.0, -7.0, 0.0, 7.0, 14.0), chandelier_height=4.3, passage_width_share=0.15,
			passage_side_gap=0.8, passage_height=3.0, passage_depth=1.6,
			stage_performers=None, performer_edge_margin=1.0, screen_width=6.0, screen_caption="RSX - RetroSfera 2027",
			screen_logo="logo1.png", logo_fill_share=0.85):
		self.half_width = half_width
		self.half_length = half_length
		self.height = height
		self.windows_per_side = windows_per_side
		self.chandelier_rows = chandelier_rows
		self.chandelier_positions = chandelier_positions
		self.chandelier_height = chandelier_height
		self.passage_width_share = passage_width_share
		self.passage_side_gap = passage_side_gap
		self.passage_height = passage_height
		self.passage_depth = passage_depth
		self.stage_performers = stage_performers or self.default_performers()
		self.performer_edge_margin = performer_edge_margin
		self.screen_width = screen_width
		self.screen_caption = screen_caption
		self.screen_logo = screen_logo
		self.logo_fill_share = logo_fill_share
		self.resources_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
		self.palette = MainHallPalette()
		self.stage = Stage(self.palette, self.passage_span()[1] + self.passage_side_gap, half_width, -half_length)
		self.ceiling = Ceiling(self.palette, half_width, half_length, height)
		self.parts = self.create_parts()
		builder = MeshBuilder()
		self.build_shell(builder)
		for part in self.parts:
			part.build(builder)
		self.display_list = builder.compile()
		self.dolls = self.create_dolls()
		self.big_screen = self.create_big_screen()

	def default_performers(self):
		return (
			StagePerformer(
				DollLook("KasiaHead.png", hair_color=(0.45, 0.33, 0.22), suit_color=(0.42, 0.29, 0.18), legs_color=(0.1, 0.1, 0.11)),
				stage_side="left", waving_arm="left",
			),
			StagePerformer(
				DollLook("AndrzejHead.png", hair_color=(0.33, 0.25, 0.18), suit_color=(0.12, 0.12, 0.13), legs_color=(0.17, 0.17, 0.2)),
				stage_side="right", waving_arm="right",
			),
		)

	def performer_x(self, stage_side):
		if stage_side == "left":
			return self.stage.left_x + self.performer_edge_margin
		return self.stage.right_x - self.performer_edge_margin

	def create_dolls(self):
		doll_z = self.stage.back_z + self.stage.depth * 0.55
		return [
			Doll(
				performer.look, self.resources_path, self.performer_x(performer.stage_side), doll_z,
				base_height=self.stage.top(), wave_phase=index * 1.3, waving_arm=performer.waving_arm,
			)
			for index, performer in enumerate(self.stage_performers)
		]

	def create_big_screen(self):
		screen = BigScreen(0.0, 0.0, 0.0, width=self.screen_width, height=self.screen_width * 9 / 16, lift=1.1, plasma=False)
		caption_font = os.path.join(self.resources_path, "fonts", "pocket_calcuatlor_tt.ttf")
		screen.display_lines([self.screen_caption], caption_font, size=96, fit_width=True)
		return screen

	def screen_position(self):
		return Vector3((self.stage.left_x + self.stage.right_x) / 2, self.stage.top(), self.stage.back_z + 0.6)

	def update(self, seconds):
		for doll in self.dolls:
			doll.update(seconds)
		self.big_screen.update(seconds)

	def start_dolls_jumping(self):
		for doll in self.dolls:
			doll.jump()

	def logo_path(self):
		return os.path.join(self.resources_path, self.screen_logo)

	def show_screen_logo(self):
		self.big_screen.display_image(self.logo_path(), fill_share=self.logo_fill_share)

	def logo_area(self):
		"""World-space centre and width of the logo on the big screen, once it has been shown."""
		left, top, width, height = self.big_screen.text_line_areas[0]
		screen = self.big_screen
		pixel_size = screen.width / screen.text_resolution[0]
		position = self.screen_position()
		center = Vector3(
			position.x - screen.width / 2 + (left + width / 2) * pixel_size,
			position.y + screen.lift + screen.height - (top + height / 2) * pixel_size,
			position.z + screen.frame_depth / 2,
		)
		return center, width * pixel_size

	def window_centers(self):
		first = self.stage.depth + 1.4
		last = 2 * self.half_length - 2.0
		step = (last - first) / (self.windows_per_side - 1)
		return [first + step * index for index in range(self.windows_per_side)]

	def create_parts(self):
		south = Vector3(0.0, 0.0, 1.0)
		east = Vector3(1.0, 0.0, 0.0)
		centers = self.window_centers()
		parts = [
			WindowedWall(self.palette, Vector3(-self.half_width, 0.0, -self.half_length), south, east, 2 * self.half_length, self.height, centers),
			WindowedWall(self.palette, Vector3(self.half_width, 0.0, -self.half_length), south, -east, 2 * self.half_length, self.height, centers),
			self.stage,
			self.ceiling,
		]
		for x in self.chandelier_rows:
			for z in self.chandelier_positions:
				parts.append(Chandelier(self.palette, x, z, self.ceiling.underside(), self.chandelier_height))
		return parts

	def build_shell(self, builder):
		width = self.half_width
		length = self.half_length
		builder.polygon(
			self.palette.parquet,
			Vector3(-width, 0.0, -length), Vector3(width, 0.0, -length), Vector3(width, 0.0, length), Vector3(-width, 0.0, length),
		)
		builder.polygon(
			self.palette.plaster,
			Vector3(-width, 0.0, length), Vector3(width, 0.0, length), Vector3(width, self.height, length), Vector3(-width, self.height, length),
		)
		builder.box(self.palette.furniture_wood, Vector3(-width, 0.0, length - 0.03), Vector3(width, 0.15, length + 0.03))
		self.build_back_wall(builder)

	def passage_span(self):
		left = -self.half_width + self.passage_side_gap
		return left, left + 2 * self.half_width * self.passage_width_share

	def build_back_wall(self, builder):
		z = -self.half_length
		width = self.half_width
		left, right = self.passage_span()
		floor = 0.0
		top = floor + self.passage_height
		pieces = (
			(-width, left, 0.0, self.height),
			(right, width, 0.0, self.height),
			(left, right, top, self.height),
			(left, right, 0.0, floor),
		)
		for x0, x1, y0, y1 in pieces:
			builder.polygon(self.palette.plaster, Vector3(x0, y0, z), Vector3(x1, y0, z), Vector3(x1, y1, z), Vector3(x0, y1, z))
		back = z - self.passage_depth
		for x in (left, right):
			builder.polygon(self.palette.plaster, Vector3(x, floor, z), Vector3(x, top, z), Vector3(x, top, back), Vector3(x, floor, back))
		builder.polygon(self.palette.plaster, Vector3(left, top, z), Vector3(right, top, z), Vector3(right, top, back), Vector3(left, top, back))
		builder.polygon(self.palette.parquet, Vector3(left, floor, z), Vector3(right, floor, z), Vector3(right, floor, back), Vector3(left, floor, back))
		builder.polygon(self.palette.shadow, Vector3(left, floor, back), Vector3(right, floor, back), Vector3(right, top, back), Vector3(left, top, back))
		builder.box(self.palette.trim, Vector3(left - 0.12, floor, z - 0.02), Vector3(left, top + 0.12, z + 0.06))
		builder.box(self.palette.trim, Vector3(right, floor, z - 0.02), Vector3(right + 0.12, top + 0.12, z + 0.06))
		builder.box(self.palette.trim, Vector3(left - 0.12, top, z - 0.02), Vector3(right + 0.12, top + 0.12, z + 0.06))

	def stage_front(self):
		return self.stage.front_z()

	def draw(self, screen_visibility=0.0):
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_TEXTURE_BIT)
		glEnable(GL_LIGHTING)
		glEnable(GL_NORMALIZE)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
		glCallList(self.display_list)
		glPopAttrib()
		for doll in self.dolls:
			doll.draw()
		if screen_visibility > 0.0:
			self.draw_big_screen(screen_visibility)

	def draw_big_screen(self, visibility):
		position = self.screen_position()
		glPushMatrix()
		glTranslatef(position.x, position.y, position.z)
		glScalef(visibility, visibility, visibility)
		self.big_screen.draw(visibility)
		glPopMatrix()

	def release(self):
		glDeleteLists(self.display_list, 1)
		for doll in self.dolls:
			doll.release()
		self.big_screen.clear_text()
		glDeleteLists(self.big_screen.display_list, 1)
		self.palette.release()
