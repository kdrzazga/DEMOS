from OpenGL.GL import *

from demos.forty_five.c64breadbox.board_parts import CylinderPart, Fuse, PhotoBlock, PrintedCircuitBoard
from demos.forty_five.c64breadbox.connectors import ControlPort, DinSocket, PowerSwitch
from demos.forty_five.c64breadbox.dil_socket import DilSocket
from demos.forty_five.c64breadbox.layout import ControlPortSpec, DinSocketSpec, PowerSwitchSpec
from demos.forty_five.c64breadbox.photo import BoardPhoto
from demos.forty_five.geometry import text_texture, textured_quad

CONNECTOR_TYPES = {DinSocketSpec: DinSocket, ControlPortSpec: ControlPort, PowerSwitchSpec: PowerSwitch}


class C64Board:

	def __init__(self, layout, marker_axis_length_cm=2.0, label_lift_cm=1.2, label_stagger_cm=0.5,
	             label_height_cm=0.35, label_cm_per_character=0.22):
		self.layout = layout
		self.marker_axis_length = marker_axis_length_cm
		self.label_lift = label_lift_cm
		self.label_stagger = label_stagger_cm
		self.label_height = label_height_cm
		self.label_cm_per_character = label_cm_per_character
		self.photo = None
		self.sockets = ()
		self._seats_by_name = {}
		self._name_textures = {}
		self._display_lists = {}

	def build(self):
		layout = self.layout
		self.photo = BoardPhoto(layout.photo_path, layout.cm_per_pixel)
		self.circuit_board = PrintedCircuitBoard(self.photo, layout.outline, layout.board_thickness_cm,
		                                         layout.board_edge_rgb)
		self.sockets = tuple(DilSocket(spec, self.photo) for spec in layout.sockets)
		self.blocks = tuple(PhotoBlock(spec, self.photo) for spec in layout.blocks)
		self.cylinders = tuple(CylinderPart(spec, self.photo) for spec in layout.cylinders)
		self.fuses = tuple(Fuse(spec, self.photo) for spec in layout.fuses)
		self.connectors = tuple(CONNECTOR_TYPES[type(spec)](spec, self.photo) for spec in layout.connectors)
		self._seats_by_name = {socket.seat.name: socket.seat for socket in self.sockets}
		self._name_textures = {name: text_texture(512, 128, (0, 0, 0, 170), [(name, 72, (255, 255, 255), (0.5, 0.5))])
		                       for name in self._seats_by_name}
		self._display_lists = {
			"opaque": self._compile(self._draw_opaque),
			"glass": self._compile(self._draw_glass),
			"seat_markers": self._compile(self._draw_seat_markers),
			"socket_names": self._compile(self._draw_socket_names),
		}

	def seat(self, name):
		return self._seats_by_name[name]

	def seats(self):
		return tuple(socket.seat for socket in self.sockets)

	def draw(self):
		glCallList(self._display_lists["opaque"])
		self._draw_blended(self._display_lists["glass"])

	def draw_seat_markers(self):
		glCallList(self._display_lists["seat_markers"])

	def draw_socket_names(self):
		self._draw_blended(self._display_lists["socket_names"])

	def destroy(self):
		for display_list in self._display_lists.values():
			glDeleteLists(display_list, 1)
		glDeleteTextures(list(self._name_textures.values()) + [self.photo.texture])
		self._display_lists = {}
		self._name_textures = {}

	@staticmethod
	def _compile(draw):
		display_list = glGenLists(1)
		glNewList(display_list, GL_COMPILE)
		draw()
		glEndList()
		return display_list

	@staticmethod
	def _draw_blended(display_list):
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glDepthMask(GL_FALSE)
		glCallList(display_list)
		glDepthMask(GL_TRUE)
		glDisable(GL_BLEND)

	def _draw_opaque(self):
		self.circuit_board.draw()
		for part in self.sockets + self.blocks + self.cylinders + self.connectors:
			part.draw()
		for fuse in self.fuses:
			fuse.draw_opaque()

	def _draw_glass(self):
		for fuse in self.fuses:
			fuse.draw_glass()

	def _draw_seat_markers(self):
		glDisable(GL_LIGHTING)
		for seat in self.seats():
			contacts = seat.contact_positions()
			glPointSize(4.0)
			glColor3f(1.0, 0.9, 0.2)
			glBegin(GL_POINTS)
			for contact_x, contact_y, contact_z in contacts[1:]:
				glVertex3f(contact_x, contact_y + 0.01, contact_z)
			glEnd()
			glPointSize(10.0)
			glColor3f(1.0, 0.15, 0.15)
			glBegin(GL_POINTS)
			pin1_x, pin1_y, pin1_z = contacts[0]
			glVertex3f(pin1_x, pin1_y + 0.01, pin1_z)
			glEnd()
			centre_x, _, centre_z = seat.centre
			glColor3f(0.2, 0.9, 1.0)
			glBegin(GL_LINES)
			glVertex3f(centre_x, seat.seat_height, centre_z)
			glVertex3f(centre_x, seat.seat_height + self.marker_axis_length, centre_z)
			glEnd()
		glPointSize(1.0)
		glEnable(GL_LIGHTING)

	def _draw_socket_names(self):
		glDisable(GL_LIGHTING)
		glColor3f(1.0, 1.0, 1.0)
		for index, seat in enumerate(self.seats()):
			centre_x, centre_y, centre_z = seat.centre
			half_width = (len(seat.name) * self.label_cm_per_character + 0.3) / 2
			bottom = centre_y + self.label_lift + (index % 2) * self.label_stagger
			top = bottom + self.label_height
			textured_quad(self._name_textures[seat.name],
			              (centre_x - half_width, bottom, centre_z), (centre_x + half_width, bottom, centre_z),
			              (centre_x + half_width, top, centre_z), (centre_x - half_width, top, centre_z))
		glEnable(GL_LIGHTING)
