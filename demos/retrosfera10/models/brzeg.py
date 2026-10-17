import math
import random

from OpenGL.GL import (
	GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GL_ENABLE_BIT, GL_FRONT_AND_BACK, GL_LIGHTING, GL_LIGHTING_BIT,
	GL_COMPILE, GL_LIGHT_MODEL_TWO_SIDE, GL_NORMALIZE, GL_TRUE, glCallList, glColorMaterial, glDeleteLists, glEnable,
	glEndList, glGenLists, glLightModeli, glNewList, glPopAttrib, glPopMatrix, glPushAttrib, glPushMatrix, glTranslatef,
)

from lib.urban.house_factory import HouseFactories
from lib.urban.city import CityEntranceSign
from lib.urban.shapes import Shapes
from lib.vegetation import Grove
from demos.retrosfera10.models.townhall import TownHall, Vector3


class HouseRow:
	def __init__(self, origin, axis, inward, length, street_width, facade_colors, randomizer, house_factory, missing_chance=0.0, flip_chance=0.0):
		self.origin = origin
		self.axis = axis
		self.inward = inward
		self.length = length
		self.street_width = street_width
		self.facade_colors = facade_colors
		self.random = randomizer
		self.missing_chance = missing_chance
		self.flip_chance = flip_chance
		self.house_factory = house_factory
		self.bay_width = 1.45
		self.window_choices = (3, 3, 4, 4, 5)
		self.minimum_windows = 2

	def facing_degrees(self):
		facing = math.degrees(math.atan2(self.inward.x, self.inward.z))
		if self.random.random() < self.flip_chance:
			return facing + 180.0
		return facing

	def segments(self):
		street_start = (self.length - self.street_width) / 2
		street_end = (self.length + self.street_width) / 2
		return (0.0, street_start), (street_end, self.length)

	def pick_window_counts(self, available):
		counts = []
		used = 0.0
		while True:
			windows = self.random.choice(self.window_choices)
			if used + windows * self.bay_width > available:
				windows = int((available - used) // self.bay_width)
				if windows >= self.minimum_windows:
					counts.append(windows)
					used += windows * self.bay_width
				return counts, used
			counts.append(windows)
			used += windows * self.bay_width

	def create_houses(self):
		houses = []
		for start, end in self.segments():
			counts, used = self.pick_window_counts(end - start)
			position = start + (end - start - used) / 2
			for windows in counts:
				if self.random.random() >= self.missing_chance:
					houses.append(self.create_house(position, windows))
				position += windows * self.bay_width
		return houses

	def create_house(self, position, windows):
		house = self.house_factory.create(
			0.0, 0.0, 0.0, self.random.choice((3, 3, 4)), windows,
			color=self.random.choice(self.facade_colors), facing=self.facing_degrees(),
			chimney_scale=self.random.uniform(0.8, 1.2),
		)
		center = self.origin + self.axis * (position + house.width / 2) - self.inward * (house.depth / 2)
		house.x = center.x
		house.z = center.z
		return house


class Brzeg:
	def __init__(self, square_half_width=26.0, square_half_depth=28.0, street_width=6.0, seed=1248,
			ring_spacing=14.0, missing_chances=(0.04, 0.12, 0.2), flip_chances=(0.15, 0.35, 0.35), sign_size=14.0,
			house_style="simple", tree_rings=((50, 75.0, 260.0), (150, 260.0, 900.0)), approach_half_width=22.0):
		self.town_hall = TownHall()
		self.center = Vector3(0.0, 0.0, 0.0)
		self.height = self.town_hall.height
		self.square_half_width = square_half_width
		self.square_half_depth = square_half_depth
		self.street_width = street_width
		self.ring_spacing = ring_spacing
		self.missing_chances = missing_chances
		self.sign_size = sign_size
		self.flip_chances = flip_chances
		self.random = random.Random(seed)
		self.house_factory = HouseFactories().create(house_style)
		self.facade_colors = (
			(0.93, 0.84, 0.62), (0.86, 0.66, 0.52), (0.72, 0.8, 0.66), (0.92, 0.9, 0.82),
			(0.84, 0.58, 0.5), (0.66, 0.76, 0.84), (0.95, 0.78, 0.55), (0.8, 0.72, 0.84),
		)
		self.houses = self.create_houses()
		self.city_sign = self.create_city_sign()
		self.tree_rings = tree_rings
		self.approach_half_width = approach_half_width
		self.grove = Grove(self.tree_positions(), seed=seed)
		self.grove_list = 0

	def create_rows(self, ring_index):
		half_width = self.square_half_width + ring_index * self.ring_spacing
		half_depth = self.square_half_depth + ring_index * self.ring_spacing
		missing_chance = self.missing_chances[ring_index]
		flip_chance = self.flip_chances[ring_index]
		east = Vector3(1.0, 0.0, 0.0)
		south = Vector3(0.0, 0.0, 1.0)
		frontages = (
			(Vector3(-half_width, 0.0, -half_depth), east, south, 2 * half_width),
			(Vector3(half_width, 0.0, half_depth), -east, -south, 2 * half_width),
			(Vector3(-half_width, 0.0, half_depth), -south, east, 2 * half_depth),
			(Vector3(half_width, 0.0, -half_depth), south, -east, 2 * half_depth),
		)
		return [
			HouseRow(origin, axis, inward, length, self.street_width, self.facade_colors, self.random, self.house_factory, missing_chance, flip_chance)
			for origin, axis, inward, length in frontages
		]

	def create_houses(self):
		houses = []
		for ring_index in range(len(self.missing_chances)):
			for row in self.create_rows(ring_index):
				houses.extend(row.create_houses())
		return houses

	def create_city_sign(self):
		outer_half_depth = self.square_half_depth + (len(self.missing_chances) - 1) * self.ring_spacing
		sign = CityEntranceSign("Brzeg", self.sign_size, "S", board_color=(246, 246, 242))
		sign.x = self.street_width / 2 + sign.board_width / 2 + 0.8
		sign.z = outer_half_depth + 10.0
		return sign

	def tree_positions(self):
		positions = []
		for count, near, far in self.tree_rings:
			ring = []
			while len(ring) < count:
				angle = self.random.uniform(0.0, math.tau)
				distance = math.sqrt(self.random.uniform(near * near, far * far))
				x, z = distance * math.cos(angle), distance * math.sin(angle)
				if z > 0.0 and abs(x - self.city_sign.x) < self.approach_half_width:
					continue
				ring.append((x, z))
			positions.extend(ring)
		return positions

	def draw_grove(self):
		if not self.grove_list:
			self.grove_list = glGenLists(1)
			glNewList(self.grove_list, GL_COMPILE)
			self.grove.draw(Shapes())
			glEndList()
		glCallList(self.grove_list)

	def draw(self):
		hall_center = self.town_hall.center
		glPushMatrix()
		glTranslatef(-hall_center.x, -hall_center.y, -hall_center.z)
		self.town_hall.draw()
		glPopMatrix()
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT)
		glEnable(GL_LIGHTING)
		glEnable(GL_NORMALIZE)
		glEnable(GL_COLOR_MATERIAL)
		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
		glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
		for house in self.houses:
			house.draw()
		self.city_sign.draw()
		self.draw_grove()
		glPopAttrib()

	def release(self):
		if self.grove_list:
			glDeleteLists(self.grove_list, 1)
			self.grove_list = 0
		for house in self.houses:
			house.release()
		self.town_hall.release()
