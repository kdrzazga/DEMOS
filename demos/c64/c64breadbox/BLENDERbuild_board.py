"""Commodore 64 breadbox motherboard (ASSY 326298 rev A) as a 3D model.

Run inside Blender (Scripting tab -> Open build_board.py -> Run Script) or headless:
    blender --background --python build_board.py

The board photo ../resources/history/board.png is the texture of the PCB and of every
part's top face, so small parts and chip markings come straight from the photo.
Writes board.blend and board.glb next to this script.
"""
import math
from dataclasses import dataclass
from pathlib import Path

import bmesh
import bpy

PHOTO_RELATIVE_PATH = Path("..", "resources", "history", "board.png")
COLLECTION_NAME = "C64_Breadbox_Board"

PIN_PITCH_MM = 2.54
PIN_WIDTH_MM = 0.5
PIN_REACH_MM = 0.8
PIN_SHOULDER_MM = 1.0
CHIP_STANDOFF_MM = 0.8
CHIP_BODY_HEIGHT_MM = 3.4
SHIELD_HEIGHT_MM = 14.0
SHIELD_WALL_MM = 0.5
RF_JACK_RADIUS_MM = 4.3
RF_JACK_HEIGHT_MM = 11.0

TOP_FACE = (4, 5, 6, 7)
BOX_FACES = ((0, 3, 2, 1), TOP_FACE, (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))
AXIS_ROTATIONS = {"x": (0.0, math.pi / 2, 0.0), "y": (math.pi / 2, 0.0, 0.0), "z": (0.0, 0.0, 0.0)}


def mm(value):
    return value / 1000.0


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
class ChipSpec:
    name: str
    rect: PixelRect
    body_material: str = "plastic"


@dataclass(frozen=True)
class BlockSpec:
    name: str
    rect: PixelRect
    height_mm: float
    side_material: str


# Board outline: main area, the strip behind the DIN sockets and cans, and the two edge-connector tabs.
BOARD_OUTLINE = (
    PixelRect(5, 95, 1662, 745),
    PixelRect(600, 45, 1662, 95),
    PixelRect(72, 45, 292, 95),  # user port fingers
    PixelRect(432, 45, 548, 95),  # cassette port fingers
)

# All DIPs stand upright in the photo; the pin count follows from the body length.
CHIPS = (
    ChipSpec("CIA1_6526", PixelRect(87, 157, 154, 360)),
    ChipSpec("CIA2_6526", PixelRect(197, 151, 261, 358)),
    ChipSpec("CPU_6510", PixelRect(742, 154, 806, 361)),
    ChipSpec("SID_6581", PixelRect(837, 386, 905, 533)),
    ChipSpec("VIC_II", PixelRect(1019, 425, 1089, 630), "ceramic"),
    ChipSpec("ROM_BASIC_901226", PixelRect(302, 155, 365, 274)),
    ChipSpec("ROM_KERNAL_901227", PixelRect(415, 152, 475, 275)),
    ChipSpec("ROM_CHAR_901225", PixelRect(522, 150, 585, 272)),
    ChipSpec("PLA_82S100", PixelRect(738, 388, 808, 530)),
    ChipSpec("RAM_4164_1", PixelRect(150, 437, 185, 520)),
    ChipSpec("RAM_4164_2", PixelRect(213, 437, 248, 520)),
    ChipSpec("RAM_4164_3", PixelRect(277, 437, 312, 520)),
    ChipSpec("RAM_4164_4", PixelRect(348, 437, 382, 520)),
    ChipSpec("RAM_4164_5", PixelRect(150, 590, 185, 672)),
    ChipSpec("RAM_4164_6", PixelRect(213, 590, 248, 672)),
    ChipSpec("RAM_4164_7", PixelRect(277, 590, 312, 672)),
    ChipSpec("RAM_4164_8", PixelRect(348, 590, 382, 672)),
    ChipSpec("Logic_01", PixelRect(665, 160, 695, 250)),
    ChipSpec("Logic_02", PixelRect(88, 437, 120, 520)),
    ChipSpec("Logic_03", PixelRect(435, 437, 468, 520)),
    ChipSpec("Logic_04", PixelRect(520, 437, 555, 520)),
    ChipSpec("Logic_05", PixelRect(597, 437, 630, 520)),
    ChipSpec("Logic_06", PixelRect(667, 437, 700, 520)),
    ChipSpec("Logic_07", PixelRect(88, 590, 115, 672)),
    ChipSpec("Logic_08", PixelRect(435, 590, 468, 672)),
    ChipSpec("Logic_09", PixelRect(520, 570, 552, 672)),
    ChipSpec("Logic_10", PixelRect(597, 598, 630, 672)),
    ChipSpec("Logic_11", PixelRect(667, 598, 700, 672)),
)

METAL_CANS = (
    BlockSpec("RF_Modulator", PixelRect(905, 30, 1172, 300), 22.0, "tin"),
    BlockSpec("Metal_Can_326116", PixelRect(1185, 30, 1508, 190), 16.0, "tin"),
)

DIN_SOCKETS = (
    BlockSpec("DIN_Serial", PixelRect(645, 30, 745, 120), 13.0, "plastic"),
    BlockSpec("DIN_Audio_Video", PixelRect(773, 30, 870, 120), 13.0, "plastic"),
)

RF_JACK = PixelRect(965, 5, 1000, 30)

VIC_SHIELD_FRAME = PixelRect(997, 352, 1517, 650)
VIC_SHIELD_DIVIDER_X = 1240

# Axial electrolytic capacitors lying on the board, length along the photo's x axis.
AXIAL_CAPACITORS = (
    ("Capacitor_Bellcon", PixelRect(1300, 290, 1470, 345)),
    ("Capacitor_Bottom_1", PixelRect(1190, 650, 1297, 692)),
    ("Capacitor_Bottom_2", PixelRect(1362, 645, 1474, 692)),
)


class PhotoMapping:
    """Converts photo pixels to world metres (board centred on the origin, top at z=0) and back to UVs."""

    def __init__(self, width_px, height_px, mm_per_pixel):
        self.width_px = width_px
        self.height_px = height_px
        self.metres_per_pixel = mm(mm_per_pixel)

    def to_world(self, x_px, y_px):
        return ((x_px - self.width_px / 2) * self.metres_per_pixel,
                (self.height_px / 2 - y_px) * self.metres_per_pixel)

    def to_uv(self, world_x, world_y):
        x_px = world_x / self.metres_per_pixel + self.width_px / 2
        y_px = self.height_px / 2 - world_y / self.metres_per_pixel
        return x_px / self.width_px, 1.0 - y_px / self.height_px

    def corners(self, rect, z_bottom, z_top):
        left, top = self.to_world(rect.left, rect.top)
        right, bottom = self.to_world(rect.right, rect.bottom)
        return (left, bottom, z_bottom), (right, top, z_top)


class MeshBuilder:
    """Collects boxes into one mesh; a box's top face can be mapped onto the board photo."""

    def __init__(self, photo_mapping, origin):
        self.photo_mapping = photo_mapping
        self.origin = origin
        self.vertices = []
        self.faces = []
        self.face_uvs = []
        self.face_slots = []
        self.materials = []

    def _slot(self, material):
        if material not in self.materials:
            self.materials.append(material)
        return self.materials.index(material)

    def add_box(self, corner_min, corner_max, side_material, top_material=None):
        (x0, y0, z0), (x1, y1, z1) = corner_min, corner_max
        corners = ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
        first_vertex = len(self.vertices)
        origin_x, origin_y, origin_z = self.origin
        self.vertices.extend((x - origin_x, y - origin_y, z - origin_z) for x, y, z in corners)
        for face in BOX_FACES:
            is_photo_top = face == TOP_FACE and top_material is not None
            self.faces.append(tuple(first_vertex + index for index in face))
            self.face_slots.append(self._slot(top_material if is_photo_top else side_material))
            if is_photo_top:
                self.face_uvs.append(tuple(self.photo_mapping.to_uv(*corners[index][:2]) for index in face))
            else:
                self.face_uvs.append(((0, 0), (1, 0), (1, 1), (0, 1)))

    def build(self, name, collection):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.faces)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for polygon, uvs, slot in zip(mesh.polygons, self.face_uvs, self.face_slots):
            polygon.material_index = slot
            for loop_index, uv in zip(polygon.loop_indices, uvs):
                uv_layer.data[loop_index].uv = uv
        for material in self.materials:
            mesh.materials.append(material)
        mesh.update()
        board_object = bpy.data.objects.new(name, mesh)
        board_object.location = self.origin
        collection.objects.link(board_object)
        return board_object


def make_material(name, color, metallic=0.0, roughness=0.5, image=None):
    existing = bpy.data.materials.get(name)
    if existing:
        bpy.data.materials.remove(existing)
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if image is not None:
        texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        texture.image = image
        material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return material


def fresh_collection(name, parent):
    existing = bpy.data.collections.get(name)
    if existing:
        for old_object in list(existing.all_objects):
            bpy.data.objects.remove(old_object, do_unlink=True)
        for child in list(existing.children_recursive):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(existing)
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


class BoardBuilder:
    def __init__(self, photo_path, mm_per_pixel=0.25, board_thickness_mm=1.6, show_shield_lid=False):
        # 0.25 mm/px: a 40-pin DIP (52 mm) is about 207 px long in the photo.
        self.photo_image = bpy.data.images.load(str(photo_path), check_existing=True)
        width_px, height_px = self.photo_image.size
        self.photo_mapping = PhotoMapping(width_px, height_px, mm_per_pixel)
        self.board_thickness = mm(board_thickness_mm)
        self.show_shield_lid = show_shield_lid
        self.materials = {
            "photo": make_material("C64_Board_Photo", (1, 1, 1), roughness=0.6, image=self.photo_image),
            "pcb_edge": make_material("C64_PCB_Edge", (0.15, 0.35, 0.12), roughness=0.7),
            "plastic": make_material("C64_Black_Plastic", (0.02, 0.02, 0.02), roughness=0.45),
            "ceramic": make_material("C64_Purple_Ceramic", (0.22, 0.1, 0.28), roughness=0.35),
            "tin": make_material("C64_Tin", (0.78, 0.78, 0.76), metallic=1.0, roughness=0.35),
            "pin": make_material("C64_Pin", (0.8, 0.8, 0.82), metallic=1.0, roughness=0.25),
            "capacitor": make_material("C64_Capacitor_Sleeve", (0.62, 0.63, 0.66), roughness=0.4),
        }
        self.board_objects = []

    def build(self):
        root = fresh_collection(COLLECTION_NAME, bpy.context.scene.collection)
        self._build_pcb(fresh_collection("PCB", root))
        chips = fresh_collection("Chips", root)
        for chip in CHIPS:
            self._build_chip(chip, chips)
        shielding = fresh_collection("Shielding", root)
        for can in METAL_CANS:
            self._build_block(can, shielding)
        self._build_rf_jack(shielding)
        self._build_vic_shield(shielding)
        connectors = fresh_collection("Connectors", root)
        for socket in DIN_SOCKETS:
            self._build_block(socket, connectors)
        capacitors = fresh_collection("Capacitors", root)
        for name, rect in AXIAL_CAPACITORS:
            self._build_axial_capacitor(name, rect, capacitors)

    def save(self, blend_path, glb_path):
        self.photo_image.pack()
        for scene_object in bpy.context.view_layer.objects:
            scene_object.select_set(False)
        for board_object in self.board_objects:
            if board_object.visible_get():
                board_object.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    def _register(self, board_object):
        self.board_objects.append(board_object)
        return board_object

    def _builder_at(self, rect):
        center_x, center_y = self.photo_mapping.to_world(*rect.center)
        return MeshBuilder(self.photo_mapping, (center_x, center_y, 0.0))

    def _build_pcb(self, collection):
        builder = MeshBuilder(self.photo_mapping, (0.0, 0.0, 0.0))
        for rect in BOARD_OUTLINE:
            builder.add_box(*self.photo_mapping.corners(rect, -self.board_thickness, 0.0),
                            self.materials["pcb_edge"], self.materials["photo"])
        self._register(builder.build("PCB_326298", collection))

    def _build_chip(self, chip, collection):
        builder = self._builder_at(chip.rect)
        body_bottom = mm(CHIP_STANDOFF_MM)
        body_top = body_bottom + mm(CHIP_BODY_HEIGHT_MM)
        builder.add_box(*self.photo_mapping.corners(chip.rect, body_bottom, body_top),
                        self.materials[chip.body_material], self.materials["photo"])
        self._add_pins(builder, chip.rect, body_bottom)
        self._register(builder.build(chip.name, collection))

    def _add_pins(self, builder, rect, body_bottom):
        (left, bottom, _), (right, top, _) = self.photo_mapping.corners(rect, 0.0, 0.0)
        pitch = mm(PIN_PITCH_MM)
        pins_per_side = max(1, round((top - bottom) / pitch))
        first_pin_y = (top + bottom) / 2 - (pins_per_side - 1) * pitch / 2
        half_width = mm(PIN_WIDTH_MM) / 2
        reach = mm(PIN_REACH_MM)
        pin_top = body_bottom + mm(PIN_SHOULDER_MM)
        for pin_index in range(pins_per_side):
            pin_y = first_pin_y + pin_index * pitch
            for pin_left, pin_right in ((left - reach, left), (right, right + reach)):
                builder.add_box((pin_left, pin_y - half_width, 0.0), (pin_right, pin_y + half_width, pin_top),
                                self.materials["pin"])

    def _build_block(self, block, collection):
        builder = self._builder_at(block.rect)
        builder.add_box(*self.photo_mapping.corners(block.rect, 0.0, mm(block.height_mm)),
                        self.materials[block.side_material], self.materials["photo"])
        self._register(builder.build(block.name, collection))

    def _build_vic_shield(self, collection):
        frame = VIC_SHIELD_FRAME
        (left, bottom, _), (right, top, height) = self.photo_mapping.corners(frame, 0.0, mm(SHIELD_HEIGHT_MM))
        wall = mm(SHIELD_WALL_MM)
        divider_x, _ = self.photo_mapping.to_world(VIC_SHIELD_DIVIDER_X, 0)
        tin = self.materials["tin"]

        frame_builder = self._builder_at(frame)
        frame_builder.add_box((left, bottom, 0.0), (right, bottom + wall, height), tin)
        frame_builder.add_box((left, top - wall, 0.0), (right, top, height), tin)
        frame_builder.add_box((left, bottom, 0.0), (left + wall, top, height), tin)
        frame_builder.add_box((right - wall, bottom, 0.0), (right, top, height), tin)
        frame_builder.add_box((divider_x - wall / 2, bottom, 0.0), (divider_x + wall / 2, top, height), tin)
        self._register(frame_builder.build("VIC_Shield_Frame", collection))

        lid_builder = self._builder_at(frame)
        lid_builder.add_box((left, bottom, height), (right, top, height + wall), tin)
        lid = self._register(lid_builder.build("VIC_Shield_Lid", collection))
        lid.hide_set(not self.show_shield_lid)
        lid.hide_render = not self.show_shield_lid

    def _build_rf_jack(self, collection):
        center_x, _ = self.photo_mapping.to_world(*RF_JACK.center)
        _, front_y = self.photo_mapping.to_world(0, RF_JACK.bottom)
        _, back_y = self.photo_mapping.to_world(0, RF_JACK.top)
        self._build_cylinder("RF_Jack", (center_x, (front_y + back_y) / 2, mm(RF_JACK_HEIGHT_MM)),
                             mm(RF_JACK_RADIUS_MM), back_y - front_y, "y", self.materials["tin"], collection)

    def _build_axial_capacitor(self, name, rect, collection):
        (left, bottom, _), (right, top, _) = self.photo_mapping.corners(rect, 0.0, 0.0)
        radius = (top - bottom) / 2
        self._build_cylinder(name, ((left + right) / 2, (top + bottom) / 2, radius),
                             radius, right - left, "x", self.materials["capacitor"], collection)

    def _build_cylinder(self, name, center, radius, length, axis, material, collection):
        mesh = bpy.data.meshes.new(name)
        cylinder_mesh = bmesh.new()
        bmesh.ops.create_cone(cylinder_mesh, cap_ends=True, segments=32,
                              radius1=radius, radius2=radius, depth=length)
        cylinder_mesh.to_mesh(mesh)
        cylinder_mesh.free()
        for polygon in mesh.polygons:
            polygon.use_smooth = abs(polygon.normal.z) < 0.5
        mesh.materials.append(material)
        cylinder_object = bpy.data.objects.new(name, mesh)
        cylinder_object.location = center
        cylinder_object.rotation_euler = AXIS_ROTATIONS[axis]
        collection.objects.link(cylinder_object)
        return self._register(cylinder_object)


def script_directory():
    script_path = Path(__file__)
    if script_path.is_absolute() and script_path.exists():
        return script_path.parent
    text = bpy.data.texts.get(script_path.name)
    if text is not None and text.filepath:
        return Path(bpy.path.abspath(text.filepath)).parent
    raise RuntimeError("Open build_board.py from disk in Blender's Text Editor before running it")


def main():
    directory = script_directory()
    board = BoardBuilder(directory / PHOTO_RELATIVE_PATH)
    board.build()
    board.save(directory / "board.blend", directory / "board.glb")


if __name__ == "__main__":
    main()
