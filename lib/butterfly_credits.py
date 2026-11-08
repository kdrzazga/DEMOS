import math
import os
import random

import pygame

from lib.animals.butterfly import Butterfly2D


class FlyingButterfly:

	def __init__(self, image, progress, crossing_seconds, flap_frequency, flap_phase, helix_phase, helix_turns):
		self.image = image
		self.progress = progress
		self.crossing_seconds = crossing_seconds
		self.flap_frequency = flap_frequency
		self.flap_phase = flap_phase
		self.helix_phase = helix_phase
		self.helix_angular_speed = 2.0 * math.pi * helix_turns / crossing_seconds

	def update(self, delta_seconds):
		self.progress += delta_seconds / self.crossing_seconds
		self.flap_phase += 2.0 * math.pi * self.flap_frequency * delta_seconds
		self.helix_phase += self.helix_angular_speed * delta_seconds

	def has_arrived(self):
		return self.progress >= 1.0

	def wing_opening(self, minimum_opening):
		return minimum_opening + (1.0 - minimum_opening) * abs(math.cos(self.flap_phase))


class ButterfliesAnim:

	def __init__(self, x, y, width, height, left_dir=False):
		self.area = pygame.Rect(x, y, width, height)
		self.left_dir = left_dir
		self.pixels_per_butterfly = 20
		self.butterfly_count = max(1, width // self.pixels_per_butterfly)
		self.variant_count = 8
		self.minimum_width_pixels = 30
		self.maximum_width_pixels = 50
		self.minimum_crossing_seconds = 4.0
		self.maximum_crossing_seconds = 8.0
		self.minimum_flap_frequency = 2.0
		self.maximum_flap_frequency = 3.5
		self.minimum_wing_opening = 0.25
		self.helix_radius_pixels = height * 0.07
		self.minimum_helix_turns = 2.0
		self.maximum_helix_turns = 4.0
		self.helix_view_tilt = 0.6
		self.helix_depth_scaling = 0.25
		self.lane_spread_pixels = height * 0.12
		self.speed_factor = 1.0
		self.random = random.Random()
		self.variants = self.create_variants()
		self.start_point, self.end_point = self.flight_endpoints()
		self.flight_length = math.hypot(self.end_point[0] - self.start_point[0], self.end_point[1] - self.start_point[1])
		self.along_direction = ((self.end_point[0] - self.start_point[0]) / self.flight_length,
								(self.end_point[1] - self.start_point[1]) / self.flight_length)
		self.across_direction = (-self.along_direction[1], self.along_direction[0])
		self.flyers = [self.create_flyer(self.random.random()) for _ in range(self.butterfly_count)]
		self.lane_offsets = [self.random.uniform(-self.lane_spread_pixels, self.lane_spread_pixels) for _ in range(self.butterfly_count)]

	def create_variants(self):
		variants = []
		for _ in range(self.variant_count):
			butterfly = Butterfly2D(self.random.randint(self.minimum_width_pixels, self.maximum_width_pixels))
			butterfly.shape.pattern.hue = self.random.uniform(0.0, 360.0)
			butterfly.render()
			variants.append(butterfly.image)
		return variants

	def flight_endpoints(self):
		margin = self.maximum_width_pixels
		low_y = self.area.top + self.area.height * 0.75
		high_y = self.area.top + self.area.height * 0.25
		left_x = self.area.left - margin
		right_x = self.area.right + margin
		if self.left_dir:
			return (right_x, low_y), (left_x, high_y)
		return (left_x, low_y), (right_x, high_y)

	def heading_degrees(self, velocity):
		return -math.degrees(math.atan2(velocity[0], -velocity[1]))

	def create_flyer(self, progress):
		return FlyingButterfly(
			self.random.choice(self.variants),
			progress,
			self.random.uniform(self.minimum_crossing_seconds, self.maximum_crossing_seconds),
			self.random.uniform(self.minimum_flap_frequency, self.maximum_flap_frequency),
			self.random.uniform(0.0, 2.0 * math.pi),
			self.random.uniform(0.0, 2.0 * math.pi),
			self.random.uniform(self.minimum_helix_turns, self.maximum_helix_turns))

	def update(self, delta_seconds):
		for index, flyer in enumerate(self.flyers):
			flyer.update(delta_seconds * self.speed_factor)
			if flyer.has_arrived():
				self.flyers[index] = self.create_flyer(0.0)
				self.lane_offsets[index] = self.random.uniform(-self.lane_spread_pixels, self.lane_spread_pixels)

	def helix_depth(self, flyer):
		return math.cos(flyer.helix_phase)

	def flyer_position(self, flyer, lane_offset):
		along_offset = self.flight_length * flyer.progress + self.helix_radius_pixels * self.helix_view_tilt * math.cos(flyer.helix_phase)
		across_offset = lane_offset + self.helix_radius_pixels * math.sin(flyer.helix_phase)
		x = self.start_point[0] + self.along_direction[0] * along_offset + self.across_direction[0] * across_offset
		y = self.start_point[1] + self.along_direction[1] * along_offset + self.across_direction[1] * across_offset
		return x, y

	def flyer_velocity(self, flyer):
		along_speed = self.flight_length / flyer.crossing_seconds
		along_speed -= self.helix_radius_pixels * self.helix_view_tilt * flyer.helix_angular_speed * math.sin(flyer.helix_phase)
		across_speed = self.helix_radius_pixels * flyer.helix_angular_speed * math.cos(flyer.helix_phase)
		return (self.along_direction[0] * along_speed + self.across_direction[0] * across_speed,
				self.along_direction[1] * along_speed + self.across_direction[1] * across_speed)

	def draw_flyer(self, surface, flyer, lane_offset):
		depth_scale = 1.0 + self.helix_depth_scaling * self.helix_depth(flyer)
		opened_width = max(1, round(flyer.image.get_width() * depth_scale * flyer.wing_opening(self.minimum_wing_opening)))
		scaled_height = max(1, round(flyer.image.get_height() * depth_scale))
		opened = pygame.transform.smoothscale(flyer.image, (opened_width, scaled_height))
		turned = pygame.transform.rotate(opened, self.heading_degrees(self.flyer_velocity(flyer)))
		surface.blit(turned, turned.get_rect(center=self.flyer_position(flyer, lane_offset)))

	def draw(self, surface):
		previous_clip = surface.get_clip()
		surface.set_clip(self.area)
		far_to_near = sorted(zip(self.flyers, self.lane_offsets), key=lambda pair: self.helix_depth(pair[0]))
		for flyer, lane_offset in far_to_near:
			self.draw_flyer(surface, flyer, lane_offset)
		surface.set_clip(previous_clip)


class ButterflyCredits:

	def __init__(self, x, y, width, height, left_dir=False):
		self.area = pygame.Rect(x, y, width, height)
		self.resources_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
		self.font_path = os.path.join(self.resources_directory, "chintzy.ttf")
		self.names_path = os.path.join(self.resources_directory, "friends-family.txt")
		self.heading_text = "Best wishes to:"
		self.panel_color = (12, 14, 32, 200)
		self.border_color = (220, 200, 150)
		self.border_width = 2
		self.text_color = (250, 238, 210)
		self.heading_color = (255, 210, 120)
		self.shadow_color = (10, 8, 20)
		self.shadow_offset = 2
		self.font_size = max(12, height // 16)
		self.heading_font_size = round(self.font_size * 1.3)
		self.line_spacing = 1.25
		self.scroll_pixels_per_second = height / 10.0
		self.butterflies = ButterfliesAnim(x, y, width, height, left_dir)
		self.line_images = self.render_lines()
		self.line_heights = [round(image.get_height() * self.line_spacing) for image in self.line_images]
		self.list_height = sum(self.line_heights)
		self.scroll_top = float(self.area.bottom)

	def read_names(self):
		with open(self.names_path, encoding="utf-8") as names_file:
			return [line.strip() for line in names_file if line.strip()]

	def render_line(self, font, text, color):
		text_image = font.render(text, True, color)
		shadow_image = font.render(text, True, self.shadow_color)
		line_image = pygame.Surface((text_image.get_width() + self.shadow_offset, text_image.get_height() + self.shadow_offset), pygame.SRCALPHA)
		line_image.blit(shadow_image, (self.shadow_offset, self.shadow_offset))
		line_image.blit(text_image, (0, 0))
		return line_image

	def render_lines(self):
		heading_font = pygame.font.Font(self.font_path, self.heading_font_size)
		name_font = pygame.font.Font(self.font_path, self.font_size)
		heading_image = self.render_line(heading_font, self.heading_text, self.heading_color)
		return [heading_image] + [self.render_line(name_font, name, self.text_color) for name in self.read_names()]

	def update(self, delta_seconds):
		self.butterflies.update(delta_seconds)
		self.scroll_top -= self.scroll_pixels_per_second * delta_seconds
		if self.scroll_top + self.list_height < self.area.top:
			self.scroll_top = float(self.area.bottom)

	def draw_lines(self, surface):
		line_top = self.scroll_top
		for line_image, line_height in zip(self.line_images, self.line_heights):
			if self.area.top - line_height < line_top < self.area.bottom:
				surface.blit(line_image, line_image.get_rect(midtop=(self.area.centerx, round(line_top))))
			line_top += line_height

	def draw(self, surface):
		surface.fill(self.panel_color, self.area)
		self.butterflies.draw(surface)
		previous_clip = surface.get_clip()
		surface.set_clip(self.area)
		self.draw_lines(surface)
		surface.set_clip(previous_clip)
		pygame.draw.rect(surface, self.border_color, self.area, self.border_width)
