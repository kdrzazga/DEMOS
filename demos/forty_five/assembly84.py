from OpenGL.GL import *

from demos.forty_five.anims.socket_move import SocketMove
from demos.forty_five.typed_label import TypedLabel


class AssemblyStep:

	def __init__(self, caption, chips_and_socket_names, board_arrival, arriving_chip=None, arrival_neighbour=None):
		self.caption = caption
		self.socket_moves = tuple(SocketMove(chip_animation, board_arrival, socket_name)
		                          for chip_animation, socket_name in chips_and_socket_names)
		self.arriving_chip = arriving_chip
		self.arrival_neighbour = arrival_neighbour


class ChipAssembly:

	def __init__(self, screen_plane):
		self.screen_plane = screen_plane
		self.caption_height = 0.6
		self.caption_bottom_margin = 0.3
		self.caption_frames_per_letter = 4
		self.hold_seconds_after_caption_without_chips = 0.5
		self.arrival_seconds = 1.2
		self.steps = ()
		self.caption_labels = ()
		self.step_index = 0
		self.phase = "idle"
		self.phase_seconds = 0.0

	@property
	def done(self):
		return self.phase == "done"

	def begin(self, steps):
		self.steps = tuple(steps)
		self.caption_labels = tuple(TypedLabel(step.caption, self.caption_height,
		                                       frames_per_letter=self.caption_frames_per_letter)
		                            for step in self.steps)
		for label in self.caption_labels:
			label.build()
		self.step_index = 0
		self._enter("typing")

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	@property
	def _current_step(self):
		return self.steps[self.step_index]

	@property
	def _current_label(self):
		return self.caption_labels[self.step_index]

	def update(self, seconds):
		self.phase_seconds += seconds
		for socket_move in self._current_step.socket_moves:
			socket_move.update(seconds)
		if self.phase == "typing":
			self._current_label.update()
			if self._current_label.finished:
				self._after_typing()
		elif self.phase == "holding" and self.phase_seconds >= self.hold_seconds_after_caption_without_chips:
			self._next_step()
		elif self.phase == "chip_arrives" and not self._current_step.arriving_chip.is_gliding:
			self._start_socket_moves()
		elif self.phase == "chips_move" and all(move.finished for move in self._current_step.socket_moves):
			self._next_step()

	def _after_typing(self):
		step = self._current_step
		if step.arriving_chip is not None:
			neighbour = step.arrival_neighbour
			parking_pose = step.arriving_chip.pose_right_of_with_tops_aligned(
				neighbour, neighbour.resting_pose, step.arriving_chip.gap_to_left_neighbour_fraction)
			step.arriving_chip.drop_in_from_top_edge_to(parking_pose, self.arrival_seconds)
			self._enter("chip_arrives")
		elif step.socket_moves:
			self._start_socket_moves()
		else:
			self._enter("holding")

	def _start_socket_moves(self):
		for socket_move in self._current_step.socket_moves:
			socket_move.start()
		self._enter("chips_move")

	def _next_step(self):
		if self.step_index + 1 < len(self.steps):
			self.step_index += 1
			self._enter("typing")
		else:
			self._enter("done")

	def draw_overlay(self):
		if self.phase in ("idle", "done"):
			return
		caption_y = -self.screen_plane.visible_height / 2 + self.caption_bottom_margin + self.caption_height / 2
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self._current_label.draw((0.0, caption_y, -self.screen_plane.camera_distance), (1.0, 0.0, 0.0),
		                         (0.0, 1.0, 0.0))
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		for label in self.caption_labels:
			label.destroy()
