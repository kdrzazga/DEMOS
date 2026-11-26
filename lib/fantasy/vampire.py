import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import catmull_rom, mottling, normalized, surface_normals, unit_or_fallback, Sculptor
from lib.animals.shark import hermite_profile
from lib.fantasy.anatomy import Jaw, Speech, smoothstep
from lib.fantasy.rig import Bone, Choreography, LabeledMesh, Skeleton, Skin, jaw_bone, mirrored, mirrored_all, \
    side_name, sided
from lib.fantasy.sorcerer import Sorcerer, SorcererModel


class CapeSwoop(Choreography):

    def strike_hold_seconds(self):
        return 0.7

    def guard(self):
        pose = {"chest": (-6.0, 0.0, 0.0), "head": (14.0, 0.0, 0.0)}
        for side in (1.0, -1.0):
            sided(pose, "upper_arm", side, -55.0, 0.0, 55.0)
            sided(pose, "forearm", side, -45.0)
            sided(pose, "hand", side, 25.0)
        sided(pose, "thigh", -1.0, -22.0)
        sided(pose, "shin", -1.0, 25.0)
        sided(pose, "foot", -1.0, -3.0)
        sided(pose, "thigh", 1.0, 12.0)
        sided(pose, "shin", 1.0, 15.0)
        sided(pose, "foot", 1.0, -8.0)
        return pose

    def punch(self):
        pose = {"chest": (24.0, 0.0, 0.0), "head": (-22.0, 0.0, 0.0), "bite": (1.0, 0.0, 0.0)}
        for side in (1.0, -1.0):
            sided(pose, "upper_arm", side, -25.0, 0.0, 85.0)
            sided(pose, "forearm", side, -20.0)
            sided(pose, "hand", side, 35.0)
        sided(pose, "thigh", -1.0, -40.0)
        sided(pose, "shin", -1.0, 42.0)
        sided(pose, "foot", -1.0, -4.0)
        sided(pose, "thigh", 1.0, 24.0)
        sided(pose, "shin", 1.0, 10.0)
        sided(pose, "foot", 1.0, -14.0)
        return pose


class PointedEars:

    def build_ear(self, side):
        base = mirrored(self.ear_base, side)
        reach = mirrored(self.ear_tip, side) - base
        facing = normalized(mirrored(self.ear_facing, side))
        across = normalized(numpy.cross(facing, reach))
        along = numpy.linspace(0.0, 1.0, self.ear_rows)[:, None]
        spread = numpy.linspace(-1.0, 1.0, self.ear_columns)[None, :]
        width = self.ear_width * (1.0 - along) ** 0.8 * (1.0 + 0.6 * along * (1.0 - along))
        cup = (self.ear_cup * (1.0 - spread ** 2)
               * numpy.sin(math.pi * numpy.clip(along * 1.15, 0.0, 1.0)) ** 0.6)
        middle = (base + reach * along[..., None] + across * (width * spread)[..., None]
                  - facing * cup[..., None])
        normals = numpy.cross(numpy.gradient(middle, axis=0), numpy.gradient(middle, axis=1))
        normals[normals @ facing < 0.0] *= -1.0
        normals = unit_or_fallback(normals, facing)
        thickness = (self.ear_thickness * (1.0 - spread ** 6) * (1.0 - along ** 6))[..., None]
        centrality = ((1.0 - spread ** 2) * (1.0 - along ** 2))[..., None]
        crease = (numpy.exp(-((spread + 0.35 * side) / 0.09) ** 2) * (along < 0.8))[..., None]
        skin = numpy.asarray(self.skin)
        inside = (skin + (numpy.asarray(self.ear_inside) - skin) * centrality) * (1.0 - 0.45 * crease)
        self.mesh.add_grid(middle + normals * thickness, normals, inside * mottling(middle, 0.04)[..., None])
        self.mesh.add_grid(middle - normals * thickness, -normals, skin * mottling(middle, 0.04)[..., None])


class VampireModel(PointedEars, SorcererModel):

    def __init__(self, seed=31):
        self.generator = numpy.random.default_rng(seed)
        self.choose_colors()
        self.cranium_center = (0.0, 1.765, 0.01)
        self.cranium_radii = (0.098, 0.108, 0.112)
        self.face_points = ((0.0, 1.74, 0.035), (0.0, 1.68, 0.05), (0.0, 1.61, 0.07), (0.0, 1.54, 0.10),
                            (0.0, 1.50, 0.125))
        self.face_profile = ((0.0, 0.094, 0.085), (0.3, 0.09, 0.088), (0.55, 0.072, 0.078), (0.8, 0.04, 0.05),
                             (1.0, 0.008, 0.012))
        self.jaw = Jaw(hinge=(0.0, 1.668, 0.02), lip_front=(0.0, 1.633, 0.15), half_width=0.088,
                       chin=(0.0, 1.50, 0.125), max_degrees=16.0)
        self.mouth_height = 1.637
        self.mouth_half_width = 0.058
        self.nose_points = ((0.0, 1.735, 0.124), (0.0, 1.71, 0.16), (0.0, 1.683, 0.19), (0.0, 1.665, 0.198))
        self.eye_center = (0.04, 1.722)
        self.eye_look = (-0.004, -0.002)
        self.brow_points = ((0.012, 1.742), (0.045, 1.758), (0.08, 1.779))
        self.ear_base = (0.088, 1.745, -0.005)
        self.ear_tip = (0.215, 1.94, -0.06)
        self.ear_facing = (0.55, 0.15, 1.0)
        self.ear_width = 0.05
        self.ear_cup = 0.018
        self.ear_thickness = 0.003
        self.ear_rows = 18
        self.ear_columns = 15
        self.hairline_front = 0.78
        self.hairline_drop = 1.15
        self.widow_peak = 0.5
        self.widow_peak_width = 0.17
        self.hair_thickness = 0.016
        self.hair_rows = 28
        self.hair_columns = 97
        self.collar_bottom = 1.55
        self.collar_height = 0.30
        self.collar_wrap = 1.9
        self.collar_points = 3.0
        self.collar_radii = ((0.10, 0.085), (0.15, 0.11))
        self.collar_center_z = -0.015
        self.collar_rows = 14
        self.collar_columns = 49
        self.cape_radii = ((1.62, 0.11, 0.10), (1.58, 0.24, 0.15), (1.52, 0.30, 0.17), (1.45, 0.32, 0.18),
                           (1.0, 0.36, 0.22), (0.07, 0.50, 0.36))
        self.cape_center_z = -0.02
        self.cape_wrap = 1.95
        self.cape_fold_count = 9.0
        self.cape_fold_depth = (0.003, 0.03)
        self.cape_arm_start = 1.58
        self.cape_arm_share = 0.55
        self.cape_thickness = 0.003
        self.cape_rows = 56
        self.cape_columns = 41
        self.shoulders = {1.0: (0.20, 1.50, -0.01), -1.0: (-0.20, 1.50, -0.01)}
        self.elbows = {1.0: (0.25, 1.22, 0.0), -1.0: (-0.25, 1.22, 0.0)}
        self.wrists = {1.0: (0.27, 0.96, 0.04), -1.0: (-0.27, 0.96, 0.04)}
        self.hand_directions = {1.0: (0.0, -1.0, 0.12), -1.0: (0.0, -1.0, 0.12)}
        self.palm_normals = {1.0: (-1.0, 0.0, 0.0), -1.0: (1.0, 0.0, 0.0)}
        self.finger_curls = {1.0: 32.0, -1.0: 32.0}
        self.finger_spreads = {1.0: 0.4, -1.0: 0.4}
        self.thumb_sides = {1.0: -1.0, -1.0: 1.0}
        self.hips = (0.09, 0.98, 0.0)
        self.knees = (0.10, 0.52, 0.03)
        self.ankles = (0.09, 0.09, 0.02)
        self.toes = (0.09, 0.03, 0.31)
        self.stride = 0.5
        self.punching_side = 1.0
        self.standing_pose = {}
        self.seat_drop = 0.075
        self.seat_reach = 0.36
        self.back_contact = -0.26
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.cloth, self.cloth_bones = self.built(self.build_cloth)
        self.body, self.body_bones = self.built(self.build_body)
        self.eyes, self.eye_bones = self.built(self.build_eyes, ("head",))
        self.cloth_looseness = self.looseness(self.cloth[0])
        heights = numpy.concatenate([part[0][:, 1] for part in (self.cloth, self.body)])
        self.bottom = float(heights.min())
        self.total_height = float(heights.max()) - self.bottom

    def choose_colors(self):
        self.skin = (0.70, 0.74, 0.84)
        self.skin_shadow = (0.55, 0.58, 0.72)
        self.ear_inside = (0.58, 0.54, 0.70)
        self.lip = (0.36, 0.22, 0.34)
        self.mouth_inside = (0.42, 0.03, 0.06)
        self.tongue = (0.72, 0.16, 0.20)
        self.fang = (0.95, 0.93, 0.84)
        self.dark_crease = (0.08, 0.06, 0.10)
        self.hair = (0.17, 0.17, 0.27)
        self.hair_shine = (0.36, 0.36, 0.50)
        self.brow = (0.14, 0.13, 0.22)
        self.eye_white = (0.93, 0.90, 0.74)
        self.iris = (0.95, 0.76, 0.20)
        self.pupil = (0.03, 0.02, 0.03)
        self.suit = (0.06, 0.05, 0.08)
        self.lapel = (0.10, 0.09, 0.13)
        self.shirt = (0.80, 0.79, 0.84)
        self.cape_outside = (0.05, 0.04, 0.06)
        self.cape_lining = (0.66, 0.05, 0.04)
        self.ruby = (0.80, 0.05, 0.08)
        self.gold = (0.78, 0.62, 0.28)
        self.trousers = (0.05, 0.045, 0.07)
        self.boot = (0.04, 0.035, 0.045)
        self.nail = (0.20, 0.18, 0.28)

    def build_skeleton(self):
        bones = [Bone("pelvis", None, ((0.0, 1.10, 0.0), (0.0, 0.5, 0.0)), 0.25, 0.0),
                 Bone("chest", "pelvis", ((0.0, 1.12, 0.0), (0.0, 1.40, 0.0), (0.0, 1.56, -0.01)), 0.22, 0.10),
                 Bone("head", "chest", ((0.0, 1.56, -0.01), (0.0, 1.70, 0.03), (0.0, 1.82, 0.05)), 0.12, 0.05),
                 jaw_bone(self.jaw, 0.03)]
        for side in (1.0, -1.0):
            wrist = numpy.asarray(self.wrists[side])
            bones.append(Bone(side_name("upper_arm", side), "chest", (self.shoulders[side], self.elbows[side]), 0.08,
                              0.07))
            bones.append(Bone(side_name("forearm", side), side_name("upper_arm", side),
                              (self.elbows[side], self.wrists[side]), 0.10, 0.05))
            bones.append(Bone(side_name("hand", side), side_name("forearm", side),
                              (wrist, wrist + normalized(self.hand_directions[side]) * 0.12), 0.06, 0.025))
            bones.append(Bone(side_name("thigh", side), "pelvis", mirrored_all((self.hips, self.knees), side), 0.08,
                              0.06))
            bones.append(Bone(side_name("shin", side), side_name("thigh", side),
                              mirrored_all((self.knees, self.ankles), side), 0.06, 0.04))
            bones.append(Bone(side_name("foot", side), side_name("shin", side),
                              mirrored_all((self.ankles, self.toes), side), 0.05, 0.03))
        return Skeleton(bones)

    @staticmethod
    def looseness(positions):
        return (numpy.clip((1.45 - positions[:, 1]) / 1.35, 0.0, 1.0) ** 1.3).astype(numpy.float32)

    def face_front(self, lateral, height):
        centers = catmull_rom(self.face_points, 96)
        along = numpy.linspace(0.0, 1.0, len(centers))
        order = numpy.argsort(centers[:, 1])
        knots, widths, depths = (numpy.array(column) for column in zip(*self.face_profile))
        place = numpy.interp(height, centers[order, 1], along[order])
        center_depth = numpy.interp(height, centers[order, 1], centers[order, 2])
        width = float(hermite_profile(knots, widths, numpy.array([place]))[0])
        depth = float(hermite_profile(knots, depths, numpy.array([place]))[0])
        return center_depth + depth * math.sqrt(max(1.0 - (lateral / width) ** 2, 0.0))

    def cranium_front(self, lateral, height):
        center_x, center_y, center_z = self.cranium_center
        radius_x, radius_y, radius_z = self.cranium_radii
        inside = 1.0 - ((lateral - center_x) / radius_x) ** 2 - ((height - center_y) / radius_y) ** 2
        return center_z + radius_z * math.sqrt(max(inside, 0.0))

    def head_front(self, lateral, height):
        return max(self.face_front(lateral, height), self.cranium_front(lateral, height))

    def on_face(self, lateral, height, lift=0.0):
        return numpy.array((lateral, height, self.head_front(lateral, height) + lift))

    def double_sheet(self, grid, outer_color, inner_color, thickness, weights=None, blend_target=None,
                     fallback=(0.0, 0.0, -1.0)):
        inside = numpy.stack((numpy.zeros(grid.shape[:2]), grid[..., 1],
                              numpy.full(grid.shape[:2], self.cape_center_z)), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, inside, False), numpy.asarray(fallback))
        if numpy.ndim(thickness):
            thickness = thickness[..., None]
        for sign, colors in ((1.0, outer_color), (-1.0, inner_color)):
            self.mesh.next_weights = weights
            self.mesh.next_blend_target = blend_target
            self.mesh.add_grid(grid + sign * normals * thickness, sign * normals, colors)

    def build_cloth(self):
        self.use_bones("chest")
        self.build_collar()
        for side in (1.0, -1.0):
            self.build_cape_half(side)

    def build_collar(self):
        rise = numpy.linspace(0.0, 1.0, self.collar_rows)[:, None]
        angle = numpy.linspace(-self.collar_wrap, self.collar_wrap, self.collar_columns)[None, :]
        teeth = 1.0 - numpy.abs(numpy.cos(angle * self.collar_points)) ** 0.5
        (bottom_x, bottom_z), (flare_x, flare_z) = self.collar_radii
        flare = rise ** 1.5 + 0.2 * (1.0 - teeth) * rise ** 3
        radius_x = bottom_x + flare_x * flare
        radius_z = bottom_z + flare_z * flare
        height = self.collar_bottom + self.collar_height * rise * (1.0 - 0.3 * teeth * rise ** 4)
        grid = numpy.stack((radius_x * numpy.sin(angle), height,
                            self.collar_center_z - radius_z * numpy.cos(angle)), axis=-1)
        outer = numpy.asarray(self.cape_outside) * mottling(grid, 0.04)[..., None]
        inner = numpy.asarray(self.cape_lining) * (0.75 + 0.25 * rise)[..., None] * mottling(grid, 0.04)[..., None]
        self.double_sheet(grid, outer, inner, 0.003)

    def build_cape_half(self, side):
        heights = numpy.linspace(self.cape_radii[0][0], self.cape_radii[-1][0], self.cape_rows)
        levels, widths, depths = (numpy.array(column)[::-1] for column in zip(*self.cape_radii))
        radius_x = numpy.interp(heights, levels, widths)[:, None]
        radius_z = numpy.interp(heights, levels, depths)[:, None]
        drop = ((heights[0] - heights) / (heights[0] - heights[-1]))[:, None]
        spread = numpy.linspace(0.0, 1.0, self.cape_columns)[None, :]
        angle = side * spread * self.cape_wrap
        wave = numpy.sin(angle * self.cape_fold_count + 0.6 * numpy.sin(angle * 3.0))
        shallow, deep = self.cape_fold_depth
        fold = wave * (shallow + (deep - shallow) * drop ** 1.2)
        grid = numpy.stack(((radius_x + fold) * numpy.sin(angle), numpy.broadcast_to(heights[:, None], fold.shape),
                            self.cape_center_z - (radius_z + fold) * numpy.cos(angle)), axis=-1)
        shade = (1.0 - 0.3 * (0.5 - 0.5 * wave)) * mottling(grid, 0.04)
        outer = numpy.asarray(self.cape_outside) * shade[..., None]
        inner = numpy.asarray(self.cape_lining) * shade[..., None]
        weights = (smoothstep((spread - 0.4) / 0.6) * smoothstep((self.cape_arm_start - heights[:, None]) / 0.15)
                   * (1.0 - self.cape_arm_share * drop))
        self.use_bones(side_name("forearm", side))
        self.double_sheet(grid, outer, inner, self.cape_thickness, weights, "chest")

    def build_body(self):
        self.use_bones("head")
        self.build_head()
        self.use_bones("head", "jaw")
        self.build_face()
        self.build_mouth()
        self.use_bones("chest", "head")
        self.sculptor.tube(((0.0, 1.48, -0.01), (0.0, 1.60, 0.0), (0.0, 1.70, 0.01)),
                           ((0.0, 0.05, 0.048), (1.0, 0.045, 0.045)), self.skin, rings=12, segments=18)
        self.use_bones("pelvis", "chest")
        self.build_suit()
        for side in (1.0, -1.0):
            self.build_arm(side)
            self.use_bones(side_name("hand", side))
            self.build_hand(side)
        for side in (1.0, -1.0):
            self.build_leg(side)

    def build_head(self):
        sculptor = self.sculptor
        sculptor.ellipsoid(self.cranium_center, (0.0, 0.0, 1.0), self.cranium_radii[2], self.cranium_radii[0],
                           self.cranium_radii[1], self.skin, up_hint=(0.0, 1.0, 0.0), rings=22, segments=26)
        self.build_hair()
        for side in (1.0, -1.0):
            self.build_ear(side)
            self.build_eye(side)
            self.build_brow(side)
            sculptor.ellipsoid(mirrored((0.062, 1.69, 0.10), side), (side * 0.4, -0.3, 1.0), 0.035, 0.025, 0.02,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.013, 1.674, 0.178), side), (0.0, -0.3, 1.0), 0.014, 0.009, 0.008,
                               self.skin)
        sculptor.tube(self.nose_points, ((0.0, 0.017, 0.015), (0.5, 0.015, 0.016), (0.85, 0.011, 0.012),
                                         (1.0, 0.006, 0.006)), self.skin, rings=18, segments=14,
                      up_hint=(0.0, 1.0, 0.0), cap_start=False)

    def build_hair(self):
        center = numpy.asarray(self.cranium_center)
        radii = numpy.asarray(self.cranium_radii)
        around = numpy.linspace(-math.pi, math.pi, self.hair_columns)[None, :]
        reach = numpy.linspace(0.0, 1.0, self.hair_rows)[:, None]
        hairline = (self.hairline_front + self.hairline_drop * smoothstep((numpy.abs(around) - 0.35) / 2.3)
                    + self.widow_peak * numpy.exp(-(around / self.widow_peak_width) ** 2))
        polar = hairline * reach
        direction = numpy.stack((numpy.sin(polar) * numpy.sin(around), numpy.cos(polar),
                                 numpy.sin(polar) * numpy.cos(around)), axis=-1)
        outward = normalized(direction / radii)
        thickness = self.hair_thickness * (1.0 - reach ** 3) + 0.0015
        grid = center + direction * radii + outward * thickness[..., None]
        normals = unit_or_fallback(surface_normals(grid, center, True), outward)
        combing = 0.5 + 0.5 * numpy.sin(grid[..., 0] * 260.0 + 8.0 * numpy.sin(grid[..., 2] * 40.0))
        sheen = numpy.clip(direction[..., 1], 0.0, 1.0)[..., None] * combing[..., None] * 0.6
        colors = numpy.asarray(self.hair) + (numpy.asarray(self.hair_shine) - numpy.asarray(self.hair)) * sheen
        self.mesh.add_grid(grid, normals, colors * mottling(grid, 0.05)[..., None])

    def build_eye(self, side):
        sculptor = self.sculptor
        lateral, height = self.eye_center
        center = self.on_face(side * lateral, height, -0.003)
        axis = normalized((side * 0.25, 0.0, 1.0))
        sculptor.ellipsoid(center, axis, 0.016, 0.03, 0.024, self.eye_white, up_hint=(0.0, 1.0, 0.0), mottle=0.0)
        look = numpy.array((self.eye_look[0], self.eye_look[1], 0.0))
        sculptor.ellipsoid(center + axis * 0.0158 + look, axis, 0.0015, 0.005, 0.006, self.pupil,
                           up_hint=(0.0, 1.0, 0.0), rings=8, segments=12, mottle=0.0)
        sculptor.ellipsoid(center + (0.0, 0.011, 0.003), axis, 0.017, 0.032, 0.014, self.skin_shadow,
                           up_hint=(-side * 0.35, 1.0, 0.0))
        sculptor.ellipsoid(center + (0.0, -0.02, 0.0), axis, 0.012, 0.026, 0.006, self.skin_shadow,
                           up_hint=(side * 0.2, 1.0, 0.0))

    def build_eyes(self):
        for side in (1.0, -1.0):
            lateral, height = self.eye_center
            center = self.on_face(side * lateral, height, -0.003)
            axis = normalized((side * 0.25, 0.0, 1.0))
            look = numpy.array((self.eye_look[0], self.eye_look[1], 0.0))
            self.sculptor.ellipsoid(center + axis * 0.0125 + look, axis, 0.004, 0.012, 0.012, self.iris,
                                    up_hint=(0.0, 1.0, 0.0), rings=10, segments=16, mottle=0.0)

    def build_brow(self, side):
        points = [self.on_face(side * lateral, height, 0.006) for lateral, height in self.brow_points]
        centers = catmull_rom(points, 16)
        thickness = numpy.linspace(0.012, 0.005, len(centers))
        self.sculptor.sweep(centers, thickness, numpy.full(len(centers), 0.007), self.brow, up_hint=(0.0, 0.0, 1.0),
                            segments=10, cap_start=True, cap_end=True, mottle=0.04)

    def build_face(self):
        self.sculptor.tube(self.face_points, self.face_profile, self.skin, rings=28, segments=28,
                           up_hint=(0.0, 0.0, 1.0))

    def mouth_curve(self, offset, count=13):
        points = []
        for lateral in numpy.linspace(-self.mouth_half_width, self.mouth_half_width, count):
            depth = self.face_front(lateral, self.mouth_height)
            points.append((lateral, self.jaw.mouth_line_height(depth) + offset, depth + 0.002))
        return catmull_rom(points, count * 3)

    def build_mouth(self):
        sculptor = self.sculptor
        self.use_bones("head", "jaw")
        sculptor.ellipsoid((0.0, 1.635, 0.078), (1.0, 0.0, 0.0), 0.058, 0.05, 0.03, self.mouth_inside,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.0)
        self.use_bones("head")
        upper = self.mouth_curve(0.003)
        sculptor.sweep(upper, numpy.full(len(upper), 0.004), numpy.full(len(upper), 0.004), self.lip,
                       up_hint=(0.0, 0.0, 1.0), segments=8, mottle=0.0)
        for side in (1.0, -1.0):
            base = numpy.array((side * 0.028, self.jaw.mouth_line_height(0.128), 0.128))
            sculptor.spike(base, (0.0, -1.0, 0.1), 0.034, 0.008, self.fang)
            sculptor.ellipsoid((side * self.mouth_half_width, self.mouth_height + 0.004,
                                self.face_front(self.mouth_half_width, self.mouth_height) - 0.002),
                               (0.0, 0.0, 1.0), 0.006, 0.006, 0.006, self.dark_crease, mottle=0.0)
        self.use_bones("jaw")
        lower = self.mouth_curve(-0.004)
        sculptor.sweep(lower, numpy.full(len(lower), 0.004), numpy.full(len(lower), 0.004), self.lip,
                       up_hint=(0.0, 0.0, 1.0), segments=8, mottle=0.0)
        sculptor.ellipsoid((0.0, 1.618, 0.08), (0.0, 0.0, 1.0), 0.045, 0.035, 0.012, self.tongue,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.03)
        for side in (1.0, -1.0):
            base = numpy.array((side * 0.04, self.jaw.mouth_line_height(0.12) - 0.012, 0.12))
            sculptor.spike(base, (0.0, 1.0, 0.05), 0.02, 0.006, self.fang)
        chin_crease = [self.on_face(lateral, height, 0.0) for lateral, height in
                       ((-0.03, 1.566), (-0.015, 1.56), (0.0, 1.558), (0.015, 1.56), (0.03, 1.566))]
        sculptor.tube(chin_crease, ((0.0, 0.002, 0.002), (0.5, 0.0035, 0.003), (1.0, 0.002, 0.002)),
                      self.dark_crease, rings=14, segments=6, up_hint=(0.0, 0.0, 1.0))

    def build_suit(self):
        sculptor = self.sculptor
        sculptor.tube(((0.0, 1.60, -0.01), (0.0, 1.40, 0.0), (0.0, 1.15, 0.0), (0.0, 0.90, 0.0)),
                      ((0.0, 0.06, 0.05), (0.12, 0.20, 0.12), (0.4, 0.18, 0.12), (0.7, 0.15, 0.11), (1.0, 0.17, 0.12)),
                      self.suit, rings=40, segments=36, up_hint=(0.0, 0.0, 1.0), cap_end=False, mottle=0.04)
        self.use_bones("pelvis")
        sculptor.ellipsoid((0.0, 0.955, 0.0), (0.0, 1.0, 0.0), 0.055, 0.165, 0.115, self.trousers,
                           up_hint=(0.0, 0.0, 1.0), mottle=0.04)
        self.use_bones("chest")
        sculptor.ellipsoid((0.0, 1.40, 0.112), (0.0, 1.0, 0.0), 0.12, 0.045, 0.014, self.shirt,
                           up_hint=(0.0, 0.0, 1.0), mottle=0.03)
        for side in (1.0, -1.0):
            path = ((side * 0.02, 1.29, 0.124), (side * 0.045, 1.40, 0.122), (side * 0.07, 1.50, 0.11))
            centers = catmull_rom(path, 16)
            sculptor.sweep(centers, numpy.full(len(centers), 0.022), numpy.full(len(centers), 0.006), self.lapel,
                           up_hint=(0.0, 0.0, 1.0), segments=10, cap_start=True, cap_end=True, mottle=0.03)
        sculptor.ellipsoid((0.0, 1.46, 0.124), (0.0, 0.0, 1.0), 0.006, 0.026, 0.03, self.gold, mottle=0.04)
        sculptor.ellipsoid((0.0, 1.46, 0.13), (0.0, 0.0, 1.0), 0.008, 0.017, 0.021, self.ruby, mottle=0.0)

    def build_arm(self, side):
        sculptor = self.sculptor
        shoulder, elbow, wrist = (numpy.asarray(point) for point in
                                  (self.shoulders[side], self.elbows[side], self.wrists[side]))
        self.use_bones(side_name("upper_arm", side))
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0, elbow), ((0.0, 0.066, 0.066), (1.0, 0.056, 0.056)),
                      self.suit, rings=16, segments=22, mottle=0.04)
        sculptor.ellipsoid(elbow, elbow - shoulder, 0.056, 0.057, 0.057, self.suit, mottle=0.04)
        self.use_bones(side_name("forearm", side))
        sculptor.tube((elbow, (elbow + wrist) / 2.0, wrist), ((0.0, 0.055, 0.055), (1.0, 0.05, 0.05)), self.suit,
                      rings=16, segments=22, mottle=0.04)
        sculptor.ellipsoid(wrist, wrist - elbow, 0.018, 0.047, 0.047, self.shirt, mottle=0.03)


class VioletVampireModel(VampireModel):

    def choose_colors(self):
        super().choose_colors()
        self.cape_outside = (0.17, 0.05, 0.26)
        self.cape_lining = (0.56, 0.26, 0.82)
        self.ruby = (0.58, 0.16, 0.86)


class Vampire(Sorcerer):

    def __init__(self, height, model=None):
        self.model = model or self.default_model()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.acting = True
        self.talking = False
        self.speech = Speech(seed=13)
        self.resting_gape = 0.4
        self.bite_degrees = 34.0
        self.cloth_flutter = 0.03
        self.flutter_per_second = 0.4
        self.hem_rest_height = 0.004
        self.eye_glow = 0.45
        self.skin_specular = (0.20, 0.22, 0.30, 1.0)
        self.skin_shininess = 24.0
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.advance = 0.0
        model = self.model
        self.ground = model.bottom
        skeleton = model.skeleton
        self.choreography = self.make_choreography()
        self.cloth_skin = Skin(model.cloth, *model.cloth_bones, skeleton)
        self.body_skin = Skin(model.body, *model.body_bones, skeleton)
        self.eye_skin = Skin(model.eyes, *model.eye_bones, skeleton)
        self.cloth_positions = model.cloth[0].copy()
        self.matrices = skeleton.matrices({}, (0.0, 0.0, 0.0))
        self.seat = None
        self.seated_ground = 0.0
        self.seat_settled = False
        self.seated_thigh_pitch = -88.0
        self.seated_knee_spread = 5.0
        self.seated_chest = (-3.0, 0.0, 0.0)
        self.seated_head = (6.0, 0.0, 0.0)
        self.seated_upper_arm = (-26.0, 0.0, 5.0)
        self.seated_forearm = -50.0
        self.seated_hand = 15.0
        self.seated_shin = 88.0
        self.seat_rest_lift = 0.004
        self.backrest_reach = 1.6
        self.pose()

    def default_model(self):
        return VampireModel()

    def make_choreography(self):
        model = self.model
        return CapeSwoop(model.standing_pose, model.stride, model.punching_side)

    def sitting_angles(self, shin_pitch):
        pose = {"chest": self.seated_chest, "head": self.seated_head}
        for side in (1.0, -1.0):
            sided(pose, "thigh", side, self.seated_thigh_pitch, self.seated_knee_spread)
            sided(pose, "shin", side, shin_pitch)
            sided(pose, "foot", side, -self.seated_thigh_pitch - shin_pitch)
            sided(pose, "upper_arm", side, *self.seated_upper_arm)
            sided(pose, "forearm", side, self.seated_forearm)
            sided(pose, "hand", side, self.seated_hand)
        return pose

    def seat_top(self):
        return self.model.hips[1] - self.model.seat_drop

    def feet_drop(self, shin_pitch):
        self.body_skin.deform(self.model.skeleton.matrices(self.sitting_angles(shin_pitch), (0.0, 0.0, 0.0)))
        return self.seat_top() - self.body_skin.lowest()

    def solved_shin(self, drop):
        low, high = 0.0, -self.seated_thigh_pitch
        if self.feet_drop(high) <= drop:
            return high
        for _ in range(24):
            middle = (low + high) / 2.0
            if self.feet_drop(middle) < drop:
                low = middle
            else:
                high = middle
        return (low + high) / 2.0

    def natural_seat(self):
        scale = self.scale()
        model = self.model
        return self.feet_drop(-self.seated_thigh_pitch) * scale, (model.seat_reach - model.back_contact) * scale

    def sit(self, chair):
        model = self.model
        scale = self.scale()
        drop = chair.seat_height / scale
        top = self.seat_top()
        self.seat = (top, chair.seat_width / 2.0 / scale, model.back_contact,
                     model.back_contact + chair.seat_depth / scale)
        self.seated_shin = self.solved_shin(drop)
        self.seated_ground = top - drop
        self.acting = False
        self.yaw = chair.yaw
        back_x, back_z = chair.back_center
        reach = scale * model.back_contact
        self.position = (back_x - reach * math.sin(chair.yaw), chair.floor, back_z - reach * math.cos(chair.yaw))
        self.seat_settled = False
        self.pose()

    def rest_on_seat(self):
        top, half_width, back, front = self.seat
        cloth = self.cloth_skin.positions
        x, y, z = cloth[:, 0], cloth[:, 1], cloth[:, 2]
        above_seat = numpy.abs(x) < half_width
        on_seat = above_seat & (z > back) & (z < front) & (y < top + self.seat_rest_lift)
        cloth[on_seat, 1] = top + self.seat_rest_lift
        against_back = above_seat & (y > top) & (y < top + self.backrest_reach) & (z < back + self.seat_rest_lift)
        cloth[against_back, 2] = back + self.seat_rest_lift

    def restart(self):
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.pose()

    def update(self, seconds):
        self.seconds += seconds
        if self.acting:
            self.act_seconds += seconds
        self.pose()

    def jaw_degrees(self, bite):
        talk = self.speech.openness(self.seconds) if self.talking else 0.0
        speaking = self.model.jaw.max_degrees * (self.resting_gape + (1.0 - self.resting_gape) * talk)
        return max(speaking, self.bite_degrees * bite)

    def pose(self):
        if self.seat is not None and self.seat_settled and not self.talking:
            return
        self.pose_cloth()
        if self.seat is not None:
            angles, self.advance = self.sitting_angles(self.seated_shin), 0.0
        elif self.acting:
            angles, self.advance = self.choreography.pose_at(self.act_seconds)
        else:
            angles, self.advance = {}, 0.0
        bite = self.cue(angles, "bite")
        angles["jaw"] = (self.jaw_degrees(bite), 0.0, 0.0)
        self.matrices = self.model.skeleton.matrices(angles, (0.0, 0.0, self.advance))
        self.cloth_skin.deform(self.matrices, self.cloth_positions)
        self.body_skin.deform(self.matrices)
        self.eye_skin.deform(self.matrices)
        self.ground = self.body_skin.lowest() if self.acting else self.model.bottom
        if self.seat is not None:
            self.ground = self.seated_ground
            self.rest_on_seat()
            self.seat_settled = True
        cape = self.cloth_skin.positions
        numpy.maximum(cape[:, 1], self.ground + self.hem_rest_height, out=cape[:, 1])

    def begin(self):
        scale = self.scale()
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(math.degrees(self.yaw), 0.0, 1.0, 0.0)
        glScalef(scale, scale, scale)
        glTranslatef(0.0, -self.ground, 0.0)
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.skin_specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.skin_shininess)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

    def render(self):
        self.begin()
        self.draw(*self.cloth_skin.arrays())
        self.draw(*self.body_skin.arrays())
        self.draw_glowing(self.eye_skin, self.model.iris, self.eye_glow)
        self.end()
