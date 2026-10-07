"""3D model of a joystick in the style of the QuickShot II.

Proportions come from the photos in resources/ (left-front, right-front,
left-back). The separate parts - base, stick, the two red fire buttons and the
cable - live in joystick_parts.py; this class assembles them and tilts the
stick.

World frame (centimetres): x to the right, y up, z toward the user, the same
as the Commodore64 and Datasette models. The base is centred on x and z and
stands on y = 0.
"""

import pygame
from OpenGL.GL import *

from demos.c64.joystick.joystick_parts import JoystickBase, JoystickCable, JoystickStick, TopButton, TriggerButton


class Joystick:

	def __init__(self, max_tilt_degrees=20.0):
		self.max_tilt_degrees = max_tilt_degrees
		self.tilt_rate = 0.3
		self.direction_keys = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
		                       pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}

		self.base = JoystickBase()
		self.stick = JoystickStick()
		self.trigger_button = TriggerButton()
		self.top_button = TopButton()
		self.buttons = (self.trigger_button, self.top_button)

		exit_x, exit_y, exit_z = self.base.cable_exit()
		self.cable_path = ((exit_x, exit_y, exit_z), (exit_x, exit_y - 0.1, exit_z - 1.0),
		                   (exit_x + 0.6, 0.6, exit_z - 2.7), (exit_x + 2.5, 0.22, exit_z - 5.2),
		                   (exit_x + 6.5, 0.22, exit_z - 5.7), (exit_x + 9.5, 0.22, exit_z - 3.2),
		                   (exit_x + 9.0, 0.22, exit_z + 1.3), (exit_x + 7.0, 0.22, exit_z + 4.3),
		                   (exit_x + 8.0, 0.22, exit_z + 7.8), (exit_x + 10.0, 0.28, exit_z + 10.1))
		self.cable = JoystickCable(self.cable_path)

		self.held_directions = set()
		self.tilt_right = 0.0
		self.tilt_toward_user = 0.0

	def press(self, pygame_key, is_down):
		for button in self.buttons:
			if button.handles(pygame_key):
				button.held = is_down
		if pygame_key in self.direction_keys:
			if is_down:
				self.held_directions.add(pygame_key)
			else:
				self.held_directions.discard(pygame_key)

	def build(self):
		"""Create the display lists of every part. Needs a GL context."""
		for part in (self.base, self.stick, *self.buttons, self.cable):
			part.build()

	def update(self):
		right = sum(self.direction_keys[key][0] for key in self.held_directions)
		toward_user = sum(self.direction_keys[key][1] for key in self.held_directions)
		self.tilt_right += (right * self.max_tilt_degrees - self.tilt_right) * self.tilt_rate
		self.tilt_toward_user += (toward_user * self.max_tilt_degrees - self.tilt_toward_user) * self.tilt_rate
		for button in self.buttons:
			button.update()

	def draw(self):
		self.base.draw()
		self.cable.draw()
		glPushMatrix()
		glTranslatef(*self.base.stick_pivot())
		glRotatef(-self.tilt_right, 0.0, 0.0, 1.0)
		glRotatef(self.tilt_toward_user, 1.0, 0.0, 0.0)
		self.stick.draw()
		for button, mount in ((self.trigger_button, self.stick.trigger_mount()),
		                      (self.top_button, self.stick.top_button_mount())):
			glPushMatrix()
			glTranslatef(*mount)
			button.draw()
			glPopMatrix()
		glPopMatrix()

	def destroy(self):
		for part in (self.base, self.stick, *self.buttons, self.cable):
			part.destroy()
