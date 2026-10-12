import math

import pygame
from OpenGL.GL import (
	GL_ALPHA_TEST, GL_AMBIENT_AND_DIFFUSE, GL_CLAMP_TO_EDGE, GL_COLOR_MATERIAL, GL_COMPILE, GL_ENABLE_BIT,
	GL_FRONT_AND_BACK, GL_GREATER, GL_LIGHTING, GL_LIGHTING_BIT, GL_LIGHT_MODEL_TWO_SIDE, GL_LINEAR, GL_NORMALIZE,
	GL_QUADS, GL_RGBA, GL_TEXTURE_2D, GL_TEXTURE_BIT, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S,
	GL_TEXTURE_WRAP_T, GL_TRUE, GL_UNSIGNED_BYTE, glAlphaFunc, glBegin, glBindTexture, glCallList, glColor3f,
	glColorMaterial, glDeleteLists, glDeleteTextures, glDisable, glEnable, glEnd, glEndList, glGenLists,
	glGenTextures, glLightModeli, glNewList, glNormal3f, glPopAttrib, glPopMatrix, glPushAttrib, glPushMatrix,
	glRotatef, glScalef, glTexCoord2f, glTexImage2D, glTexParameteri, glTranslatef, glVertex3f,
)

from demos.retrosfera10.models.townhall import Vector3


class DollLook:
	def __init__(self, head_image, hair_color, suit_color, legs_color, boots_color=(0.08, 0.08, 0.09),
			skin_color=(0.86, 0.68, 0.58)):
		self.head_image = head_image
		self.hair_color = hair_color
		self.suit_color = suit_color
		self.legs_color = legs_color
		self.boots_color = boots_color
		self.skin_color = skin_color


class HeadTexture:
	def __init__(self, image_path):
		surface = pygame.image.load(image_path)
		width, height = surface.get_size()
		pixels = pygame.image.tobytes(surface, "RGBA", True)
		self.texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)

	def release(self):
		glDeleteTextures([self.texture_id])


class DollShapes:
	def __init__(self, slices=20, stacks=14):
		self.slices = slices
		self.stacks = stacks

	def ellipsoid(self, center, radii, first_longitude=-math.pi, last_longitude=math.pi, textured=False):
		step = (last_longitude - first_longitude) / self.slices
		glBegin(GL_QUADS)
		for stack in range(self.stacks):
			for slice_index in range(self.slices):
				for stack_step, slice_step in ((0, 0), (0, 1), (1, 1), (1, 0)):
					latitude = math.pi * (stack + stack_step) / self.stacks - math.pi / 2
					longitude = first_longitude + step * (slice_index + slice_step)
					direction = Vector3(math.cos(latitude) * math.sin(longitude), math.sin(latitude), math.cos(latitude) * math.cos(longitude))
					glNormal3f(direction.x / radii.x, direction.y / radii.y, direction.z / radii.z)
					if textured:
						glTexCoord2f((direction.x + 1.0) / 2, (direction.y + 1.0) / 2)
					glVertex3f(center.x + direction.x * radii.x, center.y + direction.y * radii.y, center.z + direction.z * radii.z)
		glEnd()

	def tube(self, start, end, radius):
		axis = (end - start).normalized()
		side = Vector3(0.0, 0.0, 1.0).cross(axis).normalized()
		depth = axis.cross(side).normalized()
		glBegin(GL_QUADS)
		for slice_index in range(self.slices):
			first = math.tau * slice_index / self.slices
			second = math.tau * (slice_index + 1) / self.slices
			for base, angle in ((start, first), (start, second), (end, second), (end, first)):
				direction = side * math.cos(angle) + depth * math.sin(angle)
				glNormal3f(direction.x, direction.y, direction.z)
				point = base + direction * radius
				glVertex3f(point.x, point.y, point.z)
		glEnd()


class Doll:
	def __init__(self, look, image_folder, x, z, height=1.75, facing=0.0, base_height=0.0, wave_speed=3.0,
			wave_phase=0.0, wave_swing=20.0, wave_raise=140.0, resting_angle=10.0, waving_arm="right", jump_height=0.35,
			jump_count=3, jump_duration=1.5):
		self.look = look
		self.x = x
		self.z = z
		self.height = height
		self.facing = facing
		self.base_height = base_height
		self.wave_speed = wave_speed
		self.wave_phase = wave_phase
		self.wave_swing = wave_swing
		self.wave_raise = wave_raise
		self.resting_angle = resting_angle
		self.waving_side = -1.0 if waving_arm == "right" else 1.0
		self.jump_height = jump_height
		self.jump_count = jump_count
		self.jump_duration = jump_duration
		self.jump_start = None
		self.time = 0.0
		self.design_height = 1.17
		self.shapes = DollShapes()
		self.torso_radii = Vector3(0.17, 0.28, 0.13)
		self.leg_spread = 0.075
		self.leg_radius = 0.055
		self.boot_radii = Vector3(0.065, 0.055, 0.1)
		self.hand_radii = Vector3(0.05, 0.06, 0.05)
		self.shoulder = Vector3(0.18, 0.79, 0.0)
		self.arm_length = 0.31
		self.arm_radius = 0.048
		self.head_center = Vector3(0.0, 0.99, 0.0)
		self.head_radii = Vector3(0.17, 0.18, 0.17)
		self.head_texture = HeadTexture(f"{image_folder}/{look.head_image}")
		self.body_list = self.compile(self.build_body)
		self.arm_list = self.compile(self.build_arm)

	def update(self, seconds):
		self.time += seconds

	def jump(self):
		self.jump_start = self.time

	def jump_lift(self):
		if self.jump_start is None:
			return 0.0
		jump_time = self.time - self.jump_start
		if jump_time > self.jump_duration:
			return 0.0
		return self.jump_height * abs(math.sin(math.pi * self.jump_count * jump_time / self.jump_duration))

	def compile(self, build):
		display_list = glGenLists(1)
		glNewList(display_list, GL_COMPILE)
		build()
		glEndList()
		return display_list

	def build_body(self):
		glColor3f(*self.look.legs_color)
		for side in (-1.0, 1.0):
			self.shapes.tube(Vector3(side * self.leg_spread, 0.07, 0.0), Vector3(side * self.leg_spread, 0.42, 0.0), self.leg_radius)
		glColor3f(*self.look.boots_color)
		for side in (-1.0, 1.0):
			self.shapes.ellipsoid(Vector3(side * self.leg_spread, 0.055, 0.025), self.boot_radii)
		glColor3f(*self.look.suit_color)
		self.shapes.ellipsoid(Vector3(0.0, 0.6, 0.0), self.torso_radii)
		glColor3f(*self.look.skin_color)
		self.shapes.tube(Vector3(0.0, 0.8, 0.0), Vector3(0.0, 0.88, 0.0), 0.055)
		self.build_head()

	def build_head(self):
		glColor3f(*self.look.hair_color)
		self.shapes.ellipsoid(self.head_center, self.head_radii)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_ALPHA_TEST)
		glAlphaFunc(GL_GREATER, 0.5)
		glBindTexture(GL_TEXTURE_2D, self.head_texture.texture_id)
		glColor3f(1.0, 1.0, 1.0)
		self.shapes.ellipsoid(self.head_center, self.head_radii * 1.01, -math.pi / 2, math.pi / 2, textured=True)
		glDisable(GL_ALPHA_TEST)
		glDisable(GL_TEXTURE_2D)

	def build_arm(self):
		glColor3f(*self.look.suit_color)
		self.shapes.ellipsoid(Vector3(0.0, 0.0, 0.0), Vector3(self.arm_radius, self.arm_radius, self.arm_radius))
		self.shapes.tube(Vector3(0.0, 0.0, 0.0), Vector3(0.0, -self.arm_length, 0.0), self.arm_radius)
		glColor3f(*self.look.skin_color)
		self.shapes.ellipsoid(Vector3(0.0, -self.arm_length - 0.04, 0.0), self.hand_radii)

	def waving_angle(self):
		return self.waving_side * (self.wave_raise + self.wave_swing * math.sin(self.time * self.wave_speed + self.wave_phase))

	def draw_arm(self, side, angle):
		glPushMatrix()
		glTranslatef(side * self.shoulder.x, self.shoulder.y, self.shoulder.z)
		glRotatef(angle, 0.0, 0.0, 1.0)
		glCallList(self.arm_list)
		glPopMatrix()

	def draw(self):
		scale = self.height / self.design_height
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_TEXTURE_BIT)
		glEnable(GL_LIGHTING)
		glEnable(GL_NORMALIZE)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
		glPushMatrix()
		glTranslatef(self.x, self.base_height + self.jump_lift(), self.z)
		glRotatef(self.facing, 0.0, 1.0, 0.0)
		glScalef(scale, scale, scale)
		glCallList(self.body_list)
		self.draw_arm(-self.waving_side, -self.waving_side * self.resting_angle)
		self.draw_arm(self.waving_side, self.waving_angle())
		glPopMatrix()
		glPopAttrib()

	def release(self):
		glDeleteLists(self.body_list, 1)
		glDeleteLists(self.arm_list, 1)
		self.head_texture.release()
