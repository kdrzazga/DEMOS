import math
import os
import random

import pygame
from OpenGL.GL import (
	GL_BLEND, GL_CLAMP_TO_EDGE, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_FALSE, GL_LIGHTING,
	GL_LINEAR, GL_MODELVIEW, GL_ONE_MINUS_SRC_ALPHA, GL_POINTS, GL_PROJECTION, GL_QUADS, GL_RGBA, GL_SRC_ALPHA,
	GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TRUE,
	GL_UNSIGNED_BYTE, glBegin, glBindTexture, glBlendFunc, glClear, glClearColor, glColor3f, glColor4f, glDepthMask,
	glDisable, glEnable, glEnd, glGenTextures, glLoadIdentity, glMatrixMode, glPointSize, glPopMatrix, glPushMatrix,
	glTexCoord2f, glTexImage2D, glTexParameteri, glTranslatef, glVertex2f, glVertex3f,
)
from OpenGL.GLU import gluOrtho2D

from lib.earth import Earth
from lib.demo_phases import CameraInterpolationHelper, GeoPoint, Light, DemoPhase
from lib.typer import Typer
from demos.retrosfera10.models.townhall import Vector3


class InterPhaseDataHandover:
	def __init__(self, earth_texture_id, surface_brightness, altitude_degrees):
		self.earth_texture_id = earth_texture_id
		self.surface_brightness = surface_brightness
		self.altitude_degrees = altitude_degrees


class CosmicTimeline:
	def __init__(self, fps=60, space=3.0, letter_frames=3, line_pause_frames=12, caption_hold=2.0,
			caption_fade=1.0, travel_delay=None, travel=6.0):
		"""travel_delay None starts the flight once the caption has been typed and held for caption_hold."""
		self.fps = fps
		self.space = space
		self.letter_frames = letter_frames
		self.line_pause_frames = line_pause_frames
		self.caption_hold = caption_hold
		self.caption_fade = caption_fade
		self.travel_delay = travel_delay
		self.travel = travel


class StarField:
	def __init__(self, count=900, radius=400.0, seed=10):
		randomizer = random.Random(seed)
		self.stars = []
		for _ in range(count):
			height = randomizer.uniform(-1.0, 1.0)
			angle = randomizer.uniform(0.0, math.tau)
			ring = math.sqrt(max(0.0, 1.0 - height * height))
			position = Vector3(math.cos(angle) * ring, height, math.sin(angle) * ring) * radius
			self.stars.append((position, randomizer.uniform(0.35, 1.0), randomizer.random() < 0.15))

	def draw_group(self, point_size, bright):
		glPointSize(point_size)
		glBegin(GL_POINTS)
		for position, brightness, is_bright in self.stars:
			if is_bright == bright:
				glColor3f(brightness, brightness, brightness * 0.95)
				glVertex3f(position.x, position.y, position.z)
		glEnd()

	def draw(self, eye):
		glDisable(GL_LIGHTING)
		glDepthMask(GL_FALSE)
		glPushMatrix()
		glTranslatef(eye.x, eye.y, eye.z)
		self.draw_group(1.5, False)
		self.draw_group(2.6, True)
		glPopMatrix()
		glDepthMask(GL_TRUE)
		glEnable(GL_LIGHTING)


class EarthGeometry:
	def __init__(self, earth):
		self.earth = earth

	def direction(self, site, spin=None):
		spin = self.earth.spin if spin is None else spin
		theta = math.radians(site.longitude + 180.0)
		rho = math.radians(90.0 - site.latitude)
		x = -math.sin(theta) * math.sin(rho)
		y = math.cos(theta) * math.sin(rho)
		z = math.cos(rho)
		x, y, z = x, z, -y
		spin_angle = math.radians(spin)
		x, z = x * math.cos(spin_angle) + z * math.sin(spin_angle), -x * math.sin(spin_angle) + z * math.cos(spin_angle)
		tilt_angle = math.radians(self.earth.tilt)
		x, y = x * math.cos(tilt_angle) - y * math.sin(tilt_angle), x * math.sin(tilt_angle) + y * math.cos(tilt_angle)
		return Vector3(x, y, z)

	def north(self, site):
		here = self.direction(site)
		ahead = self.direction(GeoPoint(site.latitude + 0.5, site.longitude))
		return (ahead - here * ahead.dot(here)).normalized()

	def facing_spin(self, site, toward):
		candidates = [step * 0.5 for step in range(720)]
		return max(candidates, key=lambda spin: self.direction(site, spin).dot(toward))


class SpaceFlight:
	def __init__(self, geometry, site, start_eye, end_altitude, aim_share=0.35):
		self.geometry = geometry
		self.site = site
		self.start_eye = start_eye
		self.end_altitude = end_altitude
		self.aim_share = aim_share
		self.radius = geometry.earth.radius

	def view(self, progress):
		aim = CameraInterpolationHelper.smooth(progress / self.aim_share)
		descent = CameraInterpolationHelper.smooth(progress)
		target_direction = self.geometry.direction(self.site)
		start_direction = self.start_eye.normalized()
		start_altitude = self.start_eye.length() - self.radius
		direction = (start_direction + (target_direction - start_direction) * aim).normalized()
		altitude = start_altitude * (self.end_altitude / start_altitude) ** descent
		eye = direction * (self.radius + altitude)
		look = target_direction * (self.radius * aim)
		up = Vector3.up()
		up = (up + (self.geometry.north(self.site) - up) * aim).normalized()
		return eye, look, up


class CaptionPanel:
	def __init__(self, lines, font_path, font_size, start_time, timeline, margin, beeping=True):
		self.start_time = start_time
		self.fps = timeline.fps
		self.margin = margin
		self.beeping = beeping
		self.panel_color = (8, 14, 40, 185)
		self.border_color = (90, 200, 255, 230)
		self.border_width = max(2, font_size // 14)
		font = pygame.font.Font(font_path, font_size)
		padding = font_size // 2
		line_height = int(font.get_linesize() * 1.2)
		width = max(font.size(line)[0] for line in lines) + 2 * padding
		height = line_height * (len(lines) - 1) + font.get_height() + 2 * padding
		self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
		self.typers = []
		frame = 0
		for index, line in enumerate(lines):
			typer = Typer(frame, line, self.surface, padding, padding + index * line_height, font_size, font_path)
			typer.speed = timeline.letter_frames
			self.typers.append(typer)
			frame += len(line) * timeline.letter_frames + timeline.line_pause_frames
		self.total_frames = frame - timeline.line_pause_frames
		self.texture_id = self.create_texture()

	def create_texture(self):
		texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		return texture_id

	def duration(self):
		return self.total_frames / self.fps

	def line_end_time(self, index):
		typer = self.typers[index]
		return self.start_time + (typer.start_frame + len(typer.text) * typer.speed) / self.fps

	def last_line_end_time(self):
		return self.line_end_time(len(self.typers) - 1)

	def render_surface(self, frame):
		self.surface.fill((0, 0, 0, 0))
		outline = self.surface.get_rect()
		pygame.draw.rect(self.surface, self.panel_color, outline, border_radius=14)
		pygame.draw.rect(self.surface, self.border_color, outline, self.border_width, border_radius=14)
		for typer in self.typers:
			typer.type(frame, self.beeping)

	def upload(self):
		pixels = pygame.image.tobytes(self.surface, "RGBA", True)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.surface.get_width(), self.surface.get_height(), 0,
			GL_RGBA, GL_UNSIGNED_BYTE, pixels)

	def draw(self, time, alpha, screen_width, screen_height):
		if time < self.start_time or alpha <= 0.0:
			return
		self.render_surface(int((time - self.start_time) * self.fps))
		self.upload()
		left = self.margin
		top = screen_height - self.margin
		right = left + self.surface.get_width()
		bottom = top - self.surface.get_height()
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		gluOrtho2D(0, screen_width, 0, screen_height)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_LIGHTING)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glColor4f(1.0, 1.0, 1.0, alpha)
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0)
		glVertex2f(left, bottom)
		glTexCoord2f(1.0, 0.0)
		glVertex2f(right, bottom)
		glTexCoord2f(1.0, 1.0)
		glVertex2f(right, top)
		glTexCoord2f(0.0, 1.0)
		glVertex2f(left, top)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_BLEND)
		glEnable(GL_LIGHTING)
		glEnable(GL_DEPTH_TEST)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)


class CosmicDemoPhase(DemoPhase):
	def __init__(self, camera, soundtrack, target_site, timeline=None):
		super().__init__(camera)
		self.soundtrack = soundtrack
		self.target_site = target_site
		self.timeline = timeline or CosmicTimeline()
		self.caption_lines = ("RSX 2027", "10-lecie RETROSFERY", "14 - 16 maja 2027", "WYRUSZAMY !!!")
		self.font_path = os.path.join(
			os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "fonts", "pocket_calcuatlor_tt.ttf")
		self.light = Light(Vector3(-0.5, 0.35, 0.8), (0.2, 0.2, 0.24, 1.0), (1.0, 1.0, 0.95, 1.0))
		self.start_eye = Vector3(0.0, 6.0, 58.0)
		self.end_altitude = 0.35
		self.earth = Earth(0.0, 0.0, 0.0, radius=6.0, spin_speed=3.0, moon_orbit_scale=0.07, moon_size_boost=1.6, moon_time_scale=4.0)
		self.geometry = EarthGeometry(self.earth)
		self.stars = StarField()
		margin = max(16, camera.screen_height // 30)
		font_size = self.caption_font_size(max(18, camera.screen_height // 18), camera.screen_width - 2 * margin)
		self.caption = CaptionPanel(
			self.caption_lines, self.font_path, font_size, self.timeline.space, self.timeline, margin=margin,
		)
		self.travel_start = self.flight_start()
		self.travel_end = self.travel_start + self.timeline.travel
		self.caption_end = self.travel_start + self.timeline.caption_fade
		self.music_time = self.caption.last_line_end_time()
		self.flight = SpaceFlight(self.geometry, self.target_site, self.start_eye, self.end_altitude)
		facing = self.geometry.facing_spin(self.target_site, self.start_eye.normalized())
		facing_time = self.travel_start + self.timeline.travel * self.flight.aim_share / 2
		self.earth.spin = facing - self.earth.spin_speed * facing_time

	def flight_start(self):
		if self.timeline.travel_delay is not None:
			return self.timeline.travel_delay
		return self.timeline.space + self.caption.duration() + self.timeline.caption_hold

	def caption_font_size(self, largest_size, available_width, smallest_size=10):
		for size in range(largest_size, smallest_size, -1):
			font = pygame.font.Font(self.font_path, size)
			panel_width = max(font.size(line)[0] for line in self.caption_lines) + 2 * (size // 2)
			if panel_width <= available_width:
				return size
		return smallest_size

	def update(self, seconds):
		super().update(seconds)
		if self.elapsed >= self.music_time:
			self.soundtrack.start()
		if self.elapsed < self.travel_end:
			self.earth.update(seconds)
		else:
			self.done = True

	def show_caption_until(self, end_time):
		self.caption_end = end_time

	def caption_alpha(self, time):
		fade_start = self.caption_end - self.timeline.caption_fade
		return 1.0 - CameraInterpolationHelper.clamp((time - fade_start) / self.timeline.caption_fade)

	def draw_caption(self, time):
		"""Drawn by the demo over whichever phase is on screen, so the caption can outlast the flight."""
		if time < self.caption_end:
			self.caption.draw(time, self.caption_alpha(time), self.camera.screen_width, self.camera.screen_height)

	def render(self):
		glClearColor(0.0, 0.0, 0.0, 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply_projection(0.05, 600.0)
		progress = CameraInterpolationHelper.clamp((self.elapsed - self.travel_start) / self.timeline.travel)
		eye, target, up = self.flight.view(progress)
		self.camera.look(eye, target, up)
		self.light.apply()
		self.stars.draw(eye)
		self.earth.draw()

	def handover(self):
		return InterPhaseDataHandover(
			self.earth.surface.id,
			self.light.brightness(self.geometry.direction(self.target_site)),
			math.degrees(self.end_altitude / self.earth.radius),
		)
