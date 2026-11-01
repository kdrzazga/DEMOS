import os
from dataclasses import dataclass

from demos.forty_five.c64breadbox.dil_package import DilPackage


@dataclass(frozen=True)
class PixelRect:
	left: float
	top: float
	right: float
	bottom: float

	@property
	def center(self):
		return (self.left + self.right) / 2, (self.top + self.bottom) / 2


@dataclass(frozen=True)
class SocketSpec:
	name: str
	chip_name: str
	center_px: tuple
	package: DilPackage
	pin1_end: str = "top"


@dataclass(frozen=True)
class BlockSpec:
	name: str
	rect: PixelRect
	height_cm: float
	side_rgb: tuple


@dataclass(frozen=True)
class CylinderSpec:
	name: str
	rect: PixelRect
	axis: str
	rgb: tuple = (200, 200, 200)
	photo_textured: bool = False
	centre_height_cm: float = None


@dataclass(frozen=True)
class FuseSpec:
	name: str
	rect: PixelRect
	cap_length_px: float
	lift_cm: float
	cap_rgb: tuple
	glass_rgb: tuple
	glass_alpha: float


@dataclass(frozen=True)
class DinSocketSpec:
	name: str
	rect: PixelRect
	height_cm: float
	facing: str
	protrusion_cm: float
	pin_angles_degrees: tuple
	has_centre_pin: bool


@dataclass(frozen=True)
class ControlPortSpec:
	name: str
	rect: PixelRect
	height_cm: float
	shell_length_cm: float


@dataclass(frozen=True)
class PowerSwitchSpec:
	name: str
	body_rect: PixelRect
	housing_rect: PixelRect
	body_height_cm: float
	housing_height_cm: float
	paddle_tilt_degrees: float


@dataclass(frozen=True)
class BoardLayout:
	photo_path: str
	cm_per_pixel: float
	board_thickness_cm: float
	board_edge_rgb: tuple
	outline: tuple
	sockets: tuple
	blocks: tuple
	cylinders: tuple
	fuses: tuple
	connectors: tuple


class BoardLayoutFactory:

	@staticmethod
	def create_assy_250425():
		c64_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		ram_columns = (342.5, 467.5, 592.5, 712.5)
		ram_rows = (1027.5, 1317.5)
		ram_sockets = tuple(
			SocketSpec(f"RAM{row_index * len(ram_columns) + column_index + 1}", "4164", (column_x, row_y),
			           DilPackage.narrow(16))
			for row_index, row_y in enumerate(ram_rows)
			for column_index, column_x in enumerate(ram_columns))
		return BoardLayout(
			photo_path=os.path.join(c64_directory, "resources", "history", "c=", "board2.png"),
			cm_per_pixel=0.0124,
			board_thickness_cm=0.16,
			board_edge_rgb=(30, 75, 55),
			outline=(
				PixelRect(20, 190, 3100, 1500),
				PixelRect(180, 90, 590, 190),
				PixelRect(860, 95, 1080, 190),
				PixelRect(1170, 55, 2880, 190),
				PixelRect(2880, 85, 3100, 190),
			),
			sockets=(
				SocketSpec("CIA1", "MOS 6526", (230, 525), DilPackage.wide(40)),
				SocketSpec("CIA2", "MOS 6526", (395, 525), DilPackage.wide(40)),
				SocketSpec("ROM_CHAR", "MOS 901225-01", (577, 584), DilPackage.wide(24)),
				SocketSpec("ROM_BASIC", "MOS 901226-01", (740, 584), DilPackage.wide(24)),
				SocketSpec("ROM_KERNAL", "MOS 901227-02", (897, 584), DilPackage.wide(24)),
				SocketSpec("CPU", "MOS 6510", (1087, 525), DilPackage.wide(40)),
				SocketSpec("SID", "MOS 6581", (1285, 460), DilPackage.wide(28)),
				SocketSpec("PLA", "MOS 906114-01", (1382, 940), DilPackage.wide(28)),
				SocketSpec("VIC", "MOS 6569", (2000, 1112), DilPackage.wide(40), "left"),
			) + ram_sockets + (
				SocketSpec("U31", "U31", (2117, 952), DilPackage.narrow(16), "left"),
			),
			blocks=(
				BlockSpec("Expansion_Port", PixelRect(2260, 56, 2883, 350), 2.0, (150, 150, 148)),
				BlockSpec("RF_Modulator", PixelRect(1707, 63, 2239, 595), 2.0, (105, 100, 95)),
			),
			cylinders=(
				CylinderSpec("RF_Jack", PixelRect(1833, 21, 1903, 70), "z", (175, 172, 165), centre_height_cm=1.1),
				CylinderSpec("Capacitor_1", PixelRect(2400, 777, 2526, 1008), "z", photo_textured=True),
				CylinderSpec("Capacitor_2", PixelRect(2540, 777, 2666, 1008), "z", photo_textured=True),
				CylinderSpec("Capacitor_3", PixelRect(2680, 777, 2792, 1008), "z", photo_textured=True),
			),
			fuses=(
				FuseSpec("Fuse", PixelRect(2435, 609, 2757, 672), 100, 0.25, (200, 200, 195), (225, 235, 240), 0.3),
			),
			connectors=(
				DinSocketSpec("DIN_Serial", PixelRect(1225, 58, 1410, 240), 1.5, "back", 0.15,
				              (-120, -60, 0, 60, 120), True),
				DinSocketSpec("DIN_Audio_Video", PixelRect(1475, 58, 1645, 240), 1.5, "back", 0.15,
				              (-90, -45, 0, 45, 90), False),
				DinSocketSpec("Power_Socket", PixelRect(2965, 170, 3150, 352), 1.5, "right", 0.68,
				              (-135, -90, -45, 45, 90, 135), True),
				PowerSwitchSpec("Power_Switch", PixelRect(3035, 365, 3110, 460), PixelRect(3110, 360, 3195, 468),
				                1.0, 1.3, 12.0),
				ControlPortSpec("Control_Port_2", PixelRect(2985, 475, 3145, 710), 1.25, 0.6),
				ControlPortSpec("Control_Port_1", PixelRect(2985, 725, 3145, 965), 1.25, 0.6),
			),
		)
