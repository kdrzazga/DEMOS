import os
from dataclasses import dataclass

import pygame

from demos.forty_five.c64breadbox.layout import (ControlPortSpec, DinSocketSpec, PixelRect, PowerSwitchSpec)


@dataclass(frozen=True)
class OpeningRect:
	start: float
	end: float
	bottom: float
	top: float


@dataclass(frozen=True)
class BreadbinLayout:
	width_cm: float
	depth_cm: float
	wall_thickness_cm: float
	floor_thickness_cm: float
	seam_height_cm: float
	top_profile: tuple
	keyboard_slope_edge: int
	badge_strip_edge: int
	keyboard_back_inset_cm: float
	board_offset: tuple
	rear_openings: tuple
	right_openings: tuple
	bottom_photo_path: str
	bottom_photo_crop: PixelRect
	badge_picture_path: str
	case_rgb: tuple


class BoardToCase:

	def __init__(self, board_layout):
		self.cm_per_pixel = board_layout.cm_per_pixel
		self.width_px, self.height_px = pygame.image.load(board_layout.photo_path).get_size()
		self.offset_x = 0.0
		self.offset_z = 0.0

	def board_x(self, x_px):
		return (x_px - self.width_px / 2) * self.cm_per_pixel

	def board_z(self, y_px):
		return (y_px - self.height_px / 2) * self.cm_per_pixel

	def case_x(self, x_px):
		return self.board_x(x_px) + self.offset_x

	def case_z(self, y_px):
		return self.board_z(y_px) + self.offset_z


class BreadbinLayoutFactory:

	@staticmethod
	def create_breadbin(board_layout):
		resources_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
		pictures_directory = os.path.join(resources_directory, "parts", "chlebak")
		width, depth, wall = 40.4, 21.6, 0.25
		board_top_y = 1.2
		opening_margin = 0.15
		edge_connector_spans_px = ((180, 590), (860, 1080))
		board_to_case = BoardToCase(board_layout)
		rear_dins = [spec for spec in board_layout.connectors
		             if isinstance(spec, DinSocketSpec) and spec.facing == "back"]
		right_connectors = [spec for spec in board_layout.connectors
		                    if not (isinstance(spec, DinSocketSpec) and spec.facing == "back")]
		rear_face_z = min(board_to_case.board_z(spec.rect.top) for spec in rear_dins)
		board_to_case.offset_z = -depth / 2 + wall - rear_face_z
		right_face_x = max(board_to_case.board_x(BreadbinLayoutFactory._right_edge_px(spec))
		                   for spec in right_connectors)
		board_to_case.offset_x = width / 2 - wall - right_face_x

		rear_openings = tuple(
			OpeningRect(board_to_case.case_x(left_px), board_to_case.case_x(right_px),
			            board_top_y - board_layout.board_thickness_cm - 0.3, board_top_y + 0.35)
			for left_px, right_px in edge_connector_spans_px)
		rear_openings += tuple(
			OpeningRect(board_to_case.case_x(spec.rect.left), board_to_case.case_x(spec.rect.right),
			            board_top_y - 0.1, board_top_y + spec.height_cm + opening_margin)
			for spec in rear_dins)
		rear_openings += tuple(
			BreadbinLayoutFactory._round_jack_opening(board_to_case, spec, board_top_y, opening_margin)
			for spec in board_layout.cylinders if spec.name == "RF_Jack")
		rear_openings += tuple(
			OpeningRect(board_to_case.case_x(spec.rect.left), board_to_case.case_x(spec.rect.right),
			            board_top_y - 0.1, board_top_y + spec.height_cm + 0.1)
			for spec in board_layout.blocks if spec.name == "Expansion_Port")

		right_rects = [BreadbinLayoutFactory._footprint_px(spec) for spec in right_connectors]
		right_heights = [BreadbinLayoutFactory._height_cm(spec) for spec in right_connectors]
		right_openings = (
			OpeningRect(board_to_case.case_z(min(rect.top for rect in right_rects)) - opening_margin,
			            board_to_case.case_z(max(rect.bottom for rect in right_rects)) + opening_margin,
			            board_top_y - 0.2, board_top_y + max(right_heights) + 0.3),
		)

		return BreadbinLayout(
			width_cm=width,
			depth_cm=depth,
			wall_thickness_cm=wall,
			floor_thickness_cm=0.3,
			seam_height_cm=2.6,
			top_profile=((10.8, 3.5), (10.6, 3.85), (10.2, 3.95), (-3.2, 6.0), (-3.7, 6.9), (-4.1, 7.2),
			             (-10.2, 7.3), (-10.7, 6.9), (-10.8, 6.4)),
			keyboard_slope_edge=2,
			badge_strip_edge=5,
			keyboard_back_inset_cm=0.5,
			board_offset=(board_to_case.offset_x, board_top_y, board_to_case.offset_z),
			rear_openings=rear_openings,
			right_openings=right_openings,
			bottom_photo_path=os.path.join(pictures_directory, "bottom.jpg"),
			bottom_photo_crop=PixelRect(44, 71, 437, 270),
			badge_picture_path=os.path.join(resources_directory, "chlebak-tab.png"),
			case_rgb=(176, 170, 155),
		)

	@staticmethod
	def _footprint_px(spec):
		if isinstance(spec, PowerSwitchSpec):
			return PixelRect(spec.body_rect.left, min(spec.body_rect.top, spec.housing_rect.top),
			                 spec.housing_rect.right, max(spec.body_rect.bottom, spec.housing_rect.bottom))
		return spec.rect

	@staticmethod
	def _right_edge_px(spec):
		return BreadbinLayoutFactory._footprint_px(spec).right

	@staticmethod
	def _height_cm(spec):
		if isinstance(spec, PowerSwitchSpec):
			return max(spec.body_height_cm, spec.housing_height_cm)
		if isinstance(spec, (ControlPortSpec, DinSocketSpec)):
			return spec.height_cm
		return 0.0

	@staticmethod
	def _round_jack_opening(board_to_case, spec, board_top_y, margin):
		radius = (spec.rect.right - spec.rect.left) * board_to_case.cm_per_pixel / 2
		centre_y = board_top_y + spec.centre_height_cm
		return OpeningRect(board_to_case.case_x(spec.rect.left) - margin, board_to_case.case_x(spec.rect.right) + margin,
		                   centre_y - radius - margin, centre_y + radius + margin)
