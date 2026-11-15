from demos.forty_five.font import FONT_PATH
from lib.typing_effect.typed_label import TypedLabel

SCREEN_RIGHT_DIRECTION = (1.0, 0.0, 0.0)
SCREEN_UP_DIRECTION = (0.0, 1.0, 0.0)


def built_typed_label(text, height, frames_per_letter=4):
	label = TypedLabel(text, height, frames_per_letter=frames_per_letter, font_path=FONT_PATH)
	label.build()
	return label


def draw_label_facing_screen(label, centre_x, centre_y, screen_plane):
	label.draw((centre_x, centre_y, -screen_plane.camera_distance), SCREEN_RIGHT_DIRECTION, SCREEN_UP_DIRECTION)


class TypedLines:

	def __init__(self, labels):
		self.labels = tuple(labels)
		self.typing_index = 0

	@property
	def finished(self):
		return self.labels[-1].finished

	def restart(self):
		for label in self.labels:
			label.restart()
		self.typing_index = 0

	def update(self):
		if self.finished:
			return
		label = self.labels[self.typing_index]
		label.update()
		if label.finished and self.typing_index + 1 < len(self.labels):
			self.typing_index += 1

	def destroy(self):
		for label in self.labels:
			label.destroy()
