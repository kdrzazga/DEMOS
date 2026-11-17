import math
import random

import numpy
import pygame
from OpenGL.GL import *

VERTEX_SOURCE = """
#version 120
varying vec2 pane_point;
void main() {
	pane_point = gl_MultiTexCoord0.xy;
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

FRAGMENT_SOURCE = """
#version 120
uniform sampler2D picture;
uniform sampler2D misted_picture;
uniform sampler2D water_map;
uniform sampler2D wiped_mist;
uniform float refraction;
uniform float mist_brightness;
uniform float mist_veil;
uniform float wipe_clarity;
uniform vec2 light_direction;
uniform float blue_shade;
uniform vec3 blue_shade_color;
varying vec2 pane_point;
vec3 shaded_picture(sampler2D source, vec2 point) {
	vec3 color = texture2D(source, point).rgb;
	float brightness = dot(color, vec3(0.299, 0.587, 0.114));
	return mix(color, blue_shade_color * brightness, blue_shade);
}
void main() {
	vec4 water = texture2D(water_map, pane_point);
	float coverage = smoothstep(0.35, 0.6, water.a);
	vec2 lens = (water.rg - 0.5) * 2.0;
	float wiped = texture2D(wiped_mist, pane_point).a * wipe_clarity;
	vec3 misted = shaded_picture(misted_picture, pane_point) * mist_brightness + vec3(mist_veil);
	vec3 clear = shaded_picture(picture, pane_point);
	vec3 behind_pane = mix(misted, clear, wiped);
	vec3 through_drop = shaded_picture(picture, pane_point - lens * refraction);
	float facing_light = dot(lens, light_direction);
	float rim_shadow = dot(lens, lens) * 0.35 + clamp(-facing_light, 0.0, 1.0) * 0.3;
	float glint = smoothstep(0.45, 0.7, facing_light) * 0.55;
	through_drop = through_drop * (1.0 - rim_shadow) + vec3(glint);
	gl_FragColor = vec4(mix(behind_pane, through_drop, coverage), 1.0);
}
"""


class ShaderProgram:

	def __init__(self, vertex_source, fragment_source):
		self.program = self.link(self.compile(GL_VERTEX_SHADER, vertex_source),
		                         self.compile(GL_FRAGMENT_SHADER, fragment_source))

	@staticmethod
	def compile(kind, source):
		shader = glCreateShader(kind)
		glShaderSource(shader, source)
		glCompileShader(shader)
		if not glGetShaderiv(shader, GL_COMPILE_STATUS):
			raise RuntimeError(glGetShaderInfoLog(shader).decode())
		return shader

	@staticmethod
	def link(vertex_shader, fragment_shader):
		program = glCreateProgram()
		glAttachShader(program, vertex_shader)
		glAttachShader(program, fragment_shader)
		glLinkProgram(program)
		if not glGetProgramiv(program, GL_LINK_STATUS):
			raise RuntimeError(glGetProgramInfoLog(program).decode())
		return program

	def location(self, uniform_name):
		return glGetUniformLocation(self.program, uniform_name)

	def use(self):
		glUseProgram(self.program)

	@staticmethod
	def release():
		glUseProgram(0)


class RenderTarget:

	def __init__(self, size):
		self.size = size
		self.previous_framebuffer = 0
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, size[0], size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
		glBindTexture(GL_TEXTURE_2D, 0)
		self.framebuffer = glGenFramebuffers(1)
		self.begin()
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
		if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
			raise RuntimeError("rainy window render target is incomplete")
		self.clear((0.0, 0.0, 0.0, 0.0))
		self.end()

	def begin(self):
		self.previous_framebuffer = int(glGetIntegerv(GL_FRAMEBUFFER_BINDING))
		glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

	def end(self):
		glBindFramebuffer(GL_FRAMEBUFFER, self.previous_framebuffer)

	@staticmethod
	def clear(color):
		glClearColor(*color)
		glClear(GL_COLOR_BUFFER_BIT)


class DropletSprite:

	def __init__(self):
		self.pixels_across = 64
		self.edge_steepness = 2.2
		self.texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, self.pixels_across, self.pixels_across, 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, self.lens_pixels())
		glBindTexture(GL_TEXTURE_2D, 0)

	def lens_pixels(self):
		axis = numpy.linspace(-1.0, 1.0, self.pixels_across, dtype=numpy.float32)
		across, up = numpy.meshgrid(axis, axis)
		from_center = numpy.hypot(across, up)
		thickness = numpy.clip((1.0 - from_center) * self.edge_steepness, 0.0, 1.0)
		thickness = thickness * thickness * (3.0 - 2.0 * thickness)
		pixels = numpy.zeros((self.pixels_across, self.pixels_across, 4), dtype=numpy.float32)
		pixels[:, :, 0] = numpy.clip(0.5 + 0.5 * across, 0.0, 1.0)
		pixels[:, :, 1] = numpy.clip(0.5 + 0.5 * up, 0.0, 1.0)
		pixels[:, :, 2] = thickness
		pixels[:, :, 3] = thickness
		return numpy.ascontiguousarray((pixels * 255.0).astype(numpy.uint8))

	def bind(self):
		glBindTexture(GL_TEXTURE_2D, self.texture)


class QuadBatch:

	def __init__(self):
		self.corner_directions = numpy.array([[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]],
		                                     dtype=numpy.float32)
		self.corner_texture_points = numpy.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
		                                         dtype=numpy.float32)

	def draw(self, centers, half_sizes):
		quad_count = len(centers)
		if quad_count == 0:
			return
		corners = centers[:, None, :] + half_sizes[:, None, :] * self.corner_directions[None, :, :]
		vertices = numpy.ascontiguousarray(corners.reshape(-1, 2), dtype=numpy.float32)
		texture_points = numpy.ascontiguousarray(numpy.tile(self.corner_texture_points, (quad_count, 1)))
		glEnableClientState(GL_VERTEX_ARRAY)
		glEnableClientState(GL_TEXTURE_COORD_ARRAY)
		glVertexPointer(2, GL_FLOAT, 0, vertices)
		glTexCoordPointer(2, GL_FLOAT, 0, texture_points)
		glDrawArrays(GL_QUADS, 0, quad_count * 4)
		glDisableClientState(GL_TEXTURE_COORD_ARRAY)
		glDisableClientState(GL_VERTEX_ARRAY)

	def draw_rectangle(self, width, height):
		half_size = numpy.array([[width / 2.0, height / 2.0]], dtype=numpy.float32)
		self.draw(half_size, half_size)


class StillDroplets:

	def __init__(self):
		self.capacity = 21000
		self.touch_overlap = 0.5
		self.roundness_variation = 0.14
		self.centers = numpy.zeros((self.capacity, 2), dtype=numpy.float32)
		self.radii = numpy.zeros(self.capacity, dtype=numpy.float32)
		self.half_sizes = numpy.zeros((self.capacity, 2), dtype=numpy.float32)
		self.next_slot = 0

	def add(self, center_x, center_y, radius):
		slot = self.next_slot
		self.next_slot = (self.next_slot + 1) % self.capacity
		widening = 1.0 + random.uniform(-self.roundness_variation, self.roundness_variation)
		self.centers[slot] = (center_x, center_y)
		self.radii[slot] = radius
		self.half_sizes[slot] = (radius * widening, radius / widening)

	def absorb_around(self, center_x, center_y, reach):
		distances = numpy.hypot(self.centers[:, 0] - center_x, self.centers[:, 1] - center_y)
		touching = (self.radii > 0.0) & (distances < reach + self.radii * self.touch_overlap)
		absorbed_area = float(numpy.sum(self.radii[touching] ** 2))
		self.radii[touching] = 0.0
		return absorbed_area

	def clear(self):
		self.radii[:] = 0.0

	def quads(self):
		present = self.radii > 0.0
		return self.centers[present], self.half_sizes[present]


class RunningDrop:

	def __init__(self, center_x, center_y, radius, pixel_scale):
		self.center_x = center_x
		self.center_y = center_y
		self.radius = radius
		self.pixel_scale = pixel_scale
		self.speed = 0.0
		self.sideways_drift = 0.0
		self.stuck_seconds = random.uniform(0.0, 0.6)
		self.speed_per_radius = 20.0
		self.speed_response = 3.5
		self.fastest_speed = 420.0 * pixel_scale
		self.sticking_chance_per_second = 0.9
		self.longest_stuck_seconds = 0.8
		self.meander_strength = 5.0
		self.meander_damping = 2.5
		self.strongest_stretch = 0.7
		self.largest_radius = 22.0 * pixel_scale
		self.smallest_radius = 4.5 * pixel_scale
		self.absorbed_area_kept = 0.6
		self.trail_droplet_share = (0.16, 0.3)
		self.trail_gap_in_radii = (1.4, 4.0)
		self.distance_to_next_trail_droplet = self.next_trail_gap()

	def next_trail_gap(self):
		return self.radius * random.uniform(*self.trail_gap_in_radii)

	def update(self, seconds, still_droplets):
		self.update_speed(seconds)
		travelled = self.speed * seconds
		self.sideways_drift += random.uniform(-1.0, 1.0) * self.meander_strength * seconds
		self.sideways_drift -= self.sideways_drift * min(1.0, self.meander_damping * seconds)
		self.center_x += self.sideways_drift * travelled
		self.center_y -= travelled
		self.absorb(still_droplets)
		self.leave_trail(travelled, still_droplets)

	def update_speed(self, seconds):
		target_speed = min(self.radius * self.speed_per_radius, self.fastest_speed)
		if self.stuck_seconds > 0.0:
			self.stuck_seconds -= seconds
			target_speed = 0.0
		elif random.random() < self.sticking_chance_per_second * seconds:
			self.stuck_seconds = random.uniform(0.1, self.longest_stuck_seconds)
		self.speed += (target_speed - self.speed) * min(1.0, self.speed_response * seconds)

	def absorb(self, still_droplets):
		absorbed_area = still_droplets.absorb_around(self.center_x, self.center_y, self.radius)
		if absorbed_area > 0.0:
			grown_area = self.radius ** 2 + absorbed_area * self.absorbed_area_kept
			self.radius = min(math.sqrt(grown_area), self.largest_radius)
			self.stuck_seconds = 0.0

	def leave_trail(self, travelled, still_droplets):
		self.distance_to_next_trail_droplet -= travelled
		if self.distance_to_next_trail_droplet > 0.0:
			return
		droplet_radius = self.radius * random.uniform(*self.trail_droplet_share)
		droplet_x = self.center_x + random.uniform(-0.3, 0.3) * self.radius
		droplet_y = self.center_y + self.radius * 1.8 + droplet_radius
		still_droplets.add(droplet_x, droplet_y, droplet_radius)
		self.radius = math.sqrt(max(self.radius ** 2 - droplet_radius ** 2, 0.0))
		self.distance_to_next_trail_droplet = self.next_trail_gap()

	@property
	def stretch(self):
		return 1.0 + self.strongest_stretch * min(self.speed / self.fastest_speed, 1.0)

	@property
	def has_dried_out(self):
		return self.radius < self.smallest_radius

	@property
	def has_left_pane(self):
		return self.center_y < -self.radius * 4.0

	def body_quad(self):
		half_height = self.radius * self.stretch
		return (self.center_x, self.center_y + half_height - self.radius), (self.radius, half_height)

	def wipe_quad(self):
		half_height = self.radius * self.stretch
		return (self.center_x, self.center_y + half_height - self.radius), (self.radius * 0.95, half_height)


class RainyWindow:

	def __init__(self, picture, pane_size):
		self.pane_size = pane_size
		self.pixel_scale = pane_size[1] / 720.0
		self.droplets_per_second = 1050.0
		self.running_drops_per_second = 19.5
		self.droplets_on_start = 7500
		self.smallest_droplet_radius = 1.5 * self.pixel_scale
		self.droplet_radius_spread = 6.5 * self.pixel_scale
		self.heaviest_still_radius = 10.0 * self.pixel_scale
		self.running_drop_radius = (9.0 * self.pixel_scale, 15.0 * self.pixel_scale)
		self.mist_return_seconds = 12.0
		self.mist_downscale = 4
		self.mist_blur_radius = 7
		self.mist_brightness = 0.82
		self.mist_veil = 0.07
		self.wipe_clarity = 0.92
		self.refraction = 0.055
		self.light_direction = (-0.6, 0.8)
		self.blue_shade = 0.0
		self.blue_shade_color = (0.35, 0.7, 1.5)
		self.water_map_background = (0.5, 0.5, 0.0, 0.0)
		self.pending_droplets = 0.0
		self.pending_running_drops = 0.0
		self.pending_mist_return = 0.0
		self.still_droplets = StillDroplets()
		self.running_drops = []
		self.sprite = DropletSprite()
		self.quad_batch = QuadBatch()
		self.water_map = RenderTarget(pane_size)
		self.wiped_mist = RenderTarget(pane_size)
		fitted_picture = self.fit_picture_to_pane(picture)
		self.picture_texture = self.upload_picture(fitted_picture)
		self.misted_picture_texture = self.upload_picture(self.mist_picture(fitted_picture))
		self.shader = ShaderProgram(VERTEX_SOURCE, FRAGMENT_SOURCE)
		self.bind_samplers()
		for _ in range(self.droplets_on_start):
			self.land_droplet()

	def bind_samplers(self):
		self.shader.use()
		for texture_unit, sampler_name in enumerate(("picture", "misted_picture", "water_map", "wiped_mist")):
			glUniform1i(self.shader.location(sampler_name), texture_unit)
		self.shader.release()

	def fit_picture_to_pane(self, picture):
		picture_width, picture_height = picture.get_size()
		pane_width, pane_height = self.pane_size
		covering_scale = max(pane_width / picture_width, pane_height / picture_height)
		scaled_size = (max(pane_width, round(picture_width * covering_scale)),
		               max(pane_height, round(picture_height * covering_scale)))
		scaled_picture = pygame.transform.smoothscale(picture, scaled_size)
		fitted_picture = pygame.Surface(self.pane_size)
		fitted_picture.blit(scaled_picture, ((pane_width - scaled_size[0]) // 2, (pane_height - scaled_size[1]) // 2))
		return fitted_picture

	def mist_picture(self, fitted_picture):
		small_size = (max(1, self.pane_size[0] // self.mist_downscale),
		              max(1, self.pane_size[1] // self.mist_downscale))
		small_picture = pygame.transform.smoothscale(fitted_picture, small_size)
		return pygame.transform.gaussian_blur(small_picture, self.mist_blur_radius)

	@staticmethod
	def upload_picture(surface):
		width, height = surface.get_size()
		texture = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE,
		             pygame.image.tobytes(surface, "RGB", True))
		glBindTexture(GL_TEXTURE_2D, 0)
		return texture

	def change_rainfall(self, factor):
		self.droplets_per_second = min(max(self.droplets_per_second * factor, 5.0), 9000.0)
		self.running_drops_per_second = min(max(self.running_drops_per_second * factor, 0.1), 180.0)

	def change_blue_shade(self, step):
		self.blue_shade = round(min(max(self.blue_shade + step, 0.0), 1.0), 2)

	def dry(self):
		self.still_droplets.clear()
		self.running_drops.clear()

	def land_droplet(self):
		center_x = random.uniform(0.0, self.pane_size[0])
		center_y = random.uniform(0.0, self.pane_size[1])
		radius = self.smallest_droplet_radius + self.droplet_radius_spread * random.random() ** 3
		merged_area = radius ** 2 + self.still_droplets.absorb_around(center_x, center_y, radius)
		merged_radius = math.sqrt(merged_area)
		if merged_radius >= self.heaviest_still_radius:
			self.running_drops.append(RunningDrop(center_x, center_y, merged_radius, self.pixel_scale))
		else:
			self.still_droplets.add(center_x, center_y, merged_radius)

	def start_running_drop(self):
		center_x = random.uniform(0.0, self.pane_size[0])
		center_y = random.uniform(0.3, 1.05) * self.pane_size[1]
		radius = random.uniform(*self.running_drop_radius)
		self.running_drops.append(RunningDrop(center_x, center_y, radius, self.pixel_scale))

	def update(self, seconds):
		self.pending_mist_return += seconds / self.mist_return_seconds
		self.pending_droplets += self.droplets_per_second * seconds
		while self.pending_droplets >= 1.0:
			self.pending_droplets -= 1.0
			self.land_droplet()
		self.pending_running_drops += self.running_drops_per_second * seconds
		while self.pending_running_drops >= 1.0:
			self.pending_running_drops -= 1.0
			self.start_running_drop()
		for running_drop in self.running_drops:
			running_drop.update(seconds, self.still_droplets)
		self.settle_finished_drops()

	def settle_finished_drops(self):
		still_running = []
		for running_drop in self.running_drops:
			if running_drop.has_left_pane:
				continue
			if running_drop.has_dried_out:
				self.still_droplets.add(running_drop.center_x, running_drop.center_y, running_drop.radius)
				continue
			still_running.append(running_drop)
		self.running_drops = still_running

	@staticmethod
	def quad_arrays(quads):
		if not quads:
			empty = numpy.zeros((0, 2), dtype=numpy.float32)
			return empty, empty
		centers = numpy.array([center for center, _ in quads], dtype=numpy.float32)
		half_sizes = numpy.array([half_size for _, half_size in quads], dtype=numpy.float32)
		return centers, half_sizes

	def render(self):
		glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_VIEWPORT_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
		self.enter_pane_projection()
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_LIGHTING)
		glDisable(GL_CULL_FACE)
		glViewport(0, 0, *self.pane_size)
		self.render_water_map()
		self.render_wiped_mist()
		self.render_pane()
		self.leave_pane_projection()
		glPopAttrib()

	def enter_pane_projection(self):
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0.0, self.pane_size[0], 0.0, self.pane_size[1], -1.0, 1.0)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()

	@staticmethod
	def leave_pane_projection():
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()

	def blend_sprites_over(self):
		glEnable(GL_BLEND)
		glBlendEquation(GL_FUNC_ADD)
		glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.sprite.bind()

	def render_water_map(self):
		self.water_map.begin()
		self.water_map.clear(self.water_map_background)
		self.blend_sprites_over()
		self.quad_batch.draw(*self.still_droplets.quads())
		self.quad_batch.draw(*self.quad_arrays([drop.body_quad() for drop in self.running_drops]))
		glBindTexture(GL_TEXTURE_2D, 0)
		self.water_map.end()

	def render_wiped_mist(self):
		self.wiped_mist.begin()
		self.return_mist()
		self.blend_sprites_over()
		self.quad_batch.draw(*self.quad_arrays([drop.wipe_quad() for drop in self.running_drops]))
		glBindTexture(GL_TEXTURE_2D, 0)
		self.wiped_mist.end()

	def return_mist(self):
		colour_steps = int(self.pending_mist_return * 255.0)
		if colour_steps == 0:
			return
		self.pending_mist_return -= colour_steps / 255.0
		glDisable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendEquation(GL_FUNC_REVERSE_SUBTRACT)
		glBlendFunc(GL_ONE, GL_ONE)
		glColor4f(0.0, 0.0, 0.0, colour_steps / 255.0)
		self.quad_batch.draw_rectangle(*self.pane_size)
		glBlendEquation(GL_FUNC_ADD)

	def render_pane(self):
		glDisable(GL_BLEND)
		layers = (self.picture_texture, self.misted_picture_texture, self.water_map.texture, self.wiped_mist.texture)
		for texture_unit, texture in enumerate(layers):
			glActiveTexture(GL_TEXTURE0 + texture_unit)
			glBindTexture(GL_TEXTURE_2D, texture)
		glActiveTexture(GL_TEXTURE0)
		self.shader.use()
		glUniform1f(self.shader.location("refraction"), self.refraction)
		glUniform1f(self.shader.location("mist_brightness"), self.mist_brightness)
		glUniform1f(self.shader.location("mist_veil"), self.mist_veil)
		glUniform1f(self.shader.location("wipe_clarity"), self.wipe_clarity)
		glUniform2f(self.shader.location("light_direction"), *self.light_direction)
		glUniform1f(self.shader.location("blue_shade"), self.blue_shade)
		glUniform3f(self.shader.location("blue_shade_color"), *self.blue_shade_color)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.quad_batch.draw_rectangle(*self.pane_size)
		self.shader.release()
		for texture_unit in reversed(range(len(layers))):
			glActiveTexture(GL_TEXTURE0 + texture_unit)
			glBindTexture(GL_TEXTURE_2D, 0)
