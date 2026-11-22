import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, catmull_rom, unit_or_fallback
from lib.fantasy.anatomy import Jaw, MuscleRelief, Speech
from lib.fantasy.rig import Choreography, LabeledMesh, Skin, biped_skeleton, both_sides, jaw_bone, mirrored, \
    mirrored_all, side_name


class StoneLumps:

    def __init__(self, size, relief):
        self.size = size
        self.relief = relief
        self.crevice_darkening = 0.35
        self.vertices_per_lump = 3
        self.sharpness = 0.6

    def count_around(self, widths, heights):
        radii = (numpy.asarray(widths) + numpy.asarray(heights)) / 2.0
        radii = radii[radii > 0.0]
        median_radius = float(numpy.median(radii)) if len(radii) else self.size
        return max(4, round(2.0 * math.pi * median_radius / self.size))

    def segments(self, widths, heights):
        return self.count_around(widths, heights) * self.vertices_per_lump

    def rings(self, length):
        return math.ceil(length / self.size * self.vertices_per_lump) + 1

    def lumpiness(self, grid):
        frequency = 2.0 * math.pi / self.size
        x, y, z = grid[..., 0] * frequency, grid[..., 1] * frequency, grid[..., 2] * frequency
        coarse = numpy.abs(numpy.sin(x + 0.3 * y) * numpy.sin(y - 0.2 * z + 1.3) * numpy.sin(z + 0.4 * x + 2.1))
        fine = numpy.abs(numpy.sin(1.9 * x - y + 0.7) * numpy.sin(1.7 * y + z) * numpy.sin(2.1 * z - x + 1.1))
        return numpy.clip(0.7 * coarse + 0.45 * fine, 0.0, 1.0) ** self.sharpness

    def displace(self, grid, centers, widths, heights, around):
        lumps = self.lumpiness(grid)
        thickness = numpy.clip((widths + heights) / (4.0 * self.size), 0.0, 1.0)[:, None]
        outward = unit_or_fallback(grid - centers[:, None, :], numpy.zeros(3))
        shade = 1.0 - self.crevice_darkening * (1.0 - lumps) * thickness
        return grid + outward * (self.relief * self.size * lumps * thickness)[..., None], shade


class TrollModel:

    def __init__(self, seed=7):
        self.generator = numpy.random.default_rng(seed)
        self.skin = (0.64, 0.64, 0.55)
        self.ochre_tint = (1.18, 0.98, 0.62)
        self.teal_tint = (0.82, 0.98, 0.96)
        self.dark_crease = (0.24, 0.22, 0.19)
        self.nail = (0.44, 0.39, 0.30)
        self.teeth = (0.78, 0.72, 0.52)
        self.eye_color = (0.95, 0.45, 0.15)
        self.hair_colors = ((0.68, 0.62, 0.46), (0.52, 0.49, 0.38), (0.42, 0.42, 0.34), (0.74, 0.70, 0.55))
        self.body_lumps = StoneLumps(0.075, 0.32)
        self.limb_lumps = StoneLumps(0.05, 0.28)
        self.fine_lumps = StoneLumps(0.03, 0.22)
        self.torso_points = ((0.0, 0.40, -0.26), (0.0, 0.56, -0.20), (0.0, 0.76, -0.10), (0.0, 0.93, -0.01),
                             (0.0, 1.04, 0.04))
        self.torso_profile = ((0.0, 0.20, 0.16), (0.3, 0.24, 0.19), (0.6, 0.30, 0.19), (0.85, 0.31, 0.17),
                              (1.0, 0.18, 0.13))
        self.torso_lumps = StoneLumps(0.045, 0.2)
        self.torso_relief = MuscleRelief(anchor=self.torso_points[0], axis=(0.0, 0.64, 0.30), anchor_height=0.90,
                                         lateral_scale=1.2, vertical_scale=0.95, texture=self.torso_lumps)
        self.shoulder = (0.33, 1.00, 0.04)
        self.upper_arm_points = ((0.34, 0.99, 0.05), (0.41, 0.85, 0.06), (0.46, 0.70, 0.06))
        self.forearm_points = ((0.46, 0.70, 0.06), (0.41, 0.73, 0.26), (0.32, 0.74, 0.46))
        self.palm_center = (0.31, 0.66, 0.53)
        self.palm_axis = (0.0, -1.0, 0.4)
        self.knuckle_offsets = (-0.05, -0.017, 0.017, 0.05)
        self.finger_lengths = (0.8, 1.0, 0.95, 0.85)
        self.leg_inset = 0.07
        self.jaw = Jaw(hinge=(0.0, 1.16, 0.20), lip_front=(0.0, 1.108, 0.41), half_width=0.13,
                       chin=(0.0, 1.05, 0.36), max_degrees=16.0)
        self.mouth_cavity = (0.16, 0.07, 0.06)
        self.thigh_points = self.inward((0.20, 0.42, -0.18), (0.24, 0.53, 0.05), (0.25, 0.60, 0.25))
        self.shin_points = self.inward((0.25, 0.60, 0.25), (0.23, 0.36, 0.14), (0.21, 0.12, 0.02))
        self.toe_offsets = (-0.07, -0.035, 0.0, 0.035, 0.065)
        self.toe_lengths = (1.0, 0.9, 0.85, 0.75, 0.65)
        self.toe_radii = (0.032, 0.026, 0.025, 0.023, 0.021)
        self.head_center = (0.0, 1.24, 0.20)
        self.head_hair_count = 110
        self.wild_hair_count = 22
        self.arm_hair_count = 12
        self.hip_hair_count = 34
        self.hair_step = 0.045
        self.hair_gravity = 0.28
        self.hair_jitter = 0.18
        self.hair_root_radius = 0.009
        self.hair_tip_radius = 0.002
        self.hair_segments = 5
        self.patch_strength = 0.55
        self.colliders = [((0.0, 1.24, 0.20), 0.15), ((0.0, 1.15, 0.32), 0.10), ((0.0, 1.08, 0.08), 0.12),
                          ((0.0, 1.04, -0.06), 0.20), ((0.0, 0.88, -0.10), 0.26), ((0.0, 0.68, -0.17), 0.25),
                          ((0.0, 0.46, -0.24), 0.22)]
        for side in (1.0, -1.0):
            for center, radius in (((0.33, 1.0, 0.04), 0.15), (self.inward((0.22, 0.48, -0.06))[0], 0.14),
                                   (self.inward((0.25, 0.6, 0.25))[0], 0.12), ((0.46, 0.70, 0.06), 0.10),
                                   ((0.40, 0.85, 0.05), 0.11), ((0.39, 0.72, 0.26), 0.10)):
                self.colliders.append((tuple(mirrored(center, side)), radius))
        self.head_hair_stiffness = 0.85
        self.stride = 0.65
        self.standing_pose = {"chest": (-25.0, 0.0, 0.0), "head": (20.0, 0.0, 0.0)}
        both_sides(self.standing_pose, "upper_arm", 25.0, 0.0, 8.0)
        both_sides(self.standing_pose, "forearm", 96.0)
        both_sides(self.standing_pose, "hand", -85.0)
        both_sides(self.standing_pose, "thigh", 113.0)
        both_sides(self.standing_pose, "shin", -138.6)
        both_sides(self.standing_pose, "foot", 25.6)
        self.hair_along = []
        self.hair_phases = []
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.body, self.body_bones = self.built(self.build_body)
        self.tint_patches(self.body)
        self.eyes, self.eye_bones = self.built(self.build_eyes, ("head",))
        self.hair, self.hair_bones = self.built(self.build_hair)
        self.hair_along = numpy.concatenate(self.hair_along).astype(numpy.float32)
        self.hair_phases = numpy.concatenate(self.hair_phases).astype(numpy.float32)
        heights = numpy.concatenate((self.body[0][:, 1], self.hair[0][:, 1]))
        self.bottom = float(heights.min())
        self.total_height = float(heights.max()) - self.bottom

    def inward(self, *points):
        return tuple((point[0] - self.leg_inset, point[1], point[2]) for point in points)

    def build_skeleton(self):
        radii = {"pelvis": 0.20, "chest": 0.27, "head": 0.13, "upper_arm": 0.10, "forearm": 0.09, "thigh": 0.12,
                 "shin": 0.08, "foot": 0.07, "hand": 0.08, "waist_blend": 0.12, "neck_blend": 0.07,
                 "shoulder_blend": 0.08, "elbow_blend": 0.05, "wrist_blend": 0.04, "hip_blend": 0.08,
                 "knee_blend": 0.05, "ankle_blend": 0.03}
        return biped_skeleton(((0.0, 0.62, -0.18), (0.0, 0.30, -0.27)),
                              ((0.0, 0.62, -0.18), (0.0, 0.85, -0.07), (0.0, 1.04, 0.04)),
                              ((0.0, 1.04, 0.06), (0.0, 1.15, 0.17), (0.0, 1.24, 0.30)),
                              (self.upper_arm_points[0], self.upper_arm_points[-1]),
                              (self.forearm_points[0], self.forearm_points[-1]),
                              (self.forearm_points[-1], (0.31, 0.62, 0.55), (0.31, 0.42, 0.52)),
                              (self.thigh_points[0], self.thigh_points[-1]),
                              (self.shin_points[0], self.shin_points[-1]),
                              (self.shin_points[-1], *self.inward((0.22, 0.06, 0.10), (0.22, 0.04, 0.36))),
                              radii, (jaw_bone(self.jaw, 0.06),))

    def use_bones(self, *names):
        self.mesh.bone_group = names

    def built(self, builder, group=("pelvis",)):
        self.mesh = LabeledMesh()
        self.mesh.bone_group = group
        self.sculptor.mesh = self.mesh
        builder()
        arrays = self.mesh.arrays()
        return arrays, self.mesh.bone_labels(self.skeleton, arrays[0])

    def tint_patches(self, part):
        positions, _, colors, _ = part
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
        ochre = numpy.clip(0.5 + 0.6 * (numpy.sin(x * 7.0 + y * 3.0) * numpy.sin(y * 6.0 - z * 5.0 + 1.0)
                                        + 0.5 * numpy.sin(z * 9.0 + x * 4.0)), 0.0, 1.0) ** 2
        teal = numpy.clip(0.5 - y * 0.6 + 0.3 * numpy.sin(x * 5.0 - z * 6.0), 0.0, 1.0)
        tint = (1.0 + (numpy.asarray(self.ochre_tint) - 1.0) * (ochre * self.patch_strength)[:, None]
                + (numpy.asarray(self.teal_tint) - 1.0) * teal[:, None])
        colors *= tint.astype(numpy.float32)

    def build_body(self):
        self.use_bones("pelvis", "chest", "head", "upper_arm_r", "upper_arm_l")
        self.build_torso()
        self.use_bones("head", "jaw")
        self.build_head()
        self.build_mouth_cavity()
        for side in (1.0, -1.0):
            self.use_bones(side_name("upper_arm", side), side_name("forearm", side))
            self.build_arm(side)
            self.use_bones(side_name("forearm", side), side_name("hand", side))
            self.build_hand(side)
            self.use_bones(side_name("thigh", side), side_name("shin", side))
            self.build_leg(side)
            self.use_bones(side_name("shin", side), side_name("foot", side))
            self.build_foot(side)

    def build_torso(self):
        sculptor = self.sculptor
        sculptor.tube(self.torso_points, self.torso_profile, self.skin, up_hint=(0.0, 0.0, 1.0),
                      scales=self.torso_relief)
        sculptor.ellipsoid((0.0, 1.04, -0.06), (1.0, 0.0, 0.0), 0.26, 0.16, 0.13, self.skin,
                           scales=self.body_lumps)
        sculptor.tube(((0.0, 1.00, 0.02), (0.0, 1.09, 0.10), (0.0, 1.15, 0.17)),
                      ((0.0, 0.12, 0.11), (1.0, 0.09, 0.09)), self.skin, rings=12, segments=24,
                      up_hint=(0.0, 0.0, 1.0), cap_start=False, cap_end=False, scales=self.limb_lumps)
        for knob in range(6):
            height = 0.52 + knob * 0.09
            depth = -0.39 + knob * 0.045
            sculptor.ellipsoid((0.0, height, depth), (0.0, 1.0, 0.4), 0.035, 0.03, 0.025, self.skin,
                               up_hint=(0.0, 0.0, 1.0))
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.20, 0.85, -0.12), side), (side * -0.3, 1.0, -0.2), 0.18, 0.09, 0.08,
                               self.skin, up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)
            sculptor.ellipsoid(mirrored(self.shoulder, side), (side * 0.3, -1.0, 0.3), 0.13, 0.13, 0.12, self.skin,
                               up_hint=(0.0, 0.0, 1.0), rings=20, segments=24, scales=self.body_lumps)

    def build_head(self):
        sculptor = self.sculptor
        sculptor.ellipsoid(self.head_center, (0.0, 0.35, 1.0), 0.14, 0.12, 0.12, self.skin, up_hint=(0.0, 1.0, 0.0),
                           scales=self.fine_lumps)
        sculptor.ellipsoid((0.0, 1.27, 0.32), (1.0, 0.0, 0.0), 0.11, 0.04, 0.035, self.skin, scales=self.fine_lumps)
        sculptor.ellipsoid((0.0, 1.15, 0.32), (0.0, -0.25, 1.0), 0.10, 0.10, 0.075, self.skin,
                           up_hint=(0.0, 1.0, 0.0), scales=self.fine_lumps)
        sculptor.ellipsoid((0.0, 1.23, 0.37), (0.0, -0.6, 1.0), 0.04, 0.025, 0.02, self.skin)
        sculptor.ellipsoid((0.0, 1.20, 0.40), (1.0, 0.0, 0.0), 0.045, 0.03, 0.035, self.skin)
        sculptor.ellipsoid((0.0, 1.125, 0.405), (1.0, 0.0, 0.0), 0.06, 0.018, 0.014, self.skin)
        sculptor.ellipsoid((0.0, 1.07, 0.35), (0.0, -0.5, 1.0), 0.06, 0.07, 0.05, self.skin, up_hint=(0.0, 1.0, 0.0),
                           scales=self.fine_lumps)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.02, 1.185, 0.425), side), (0.0, 0.0, 1.0), 0.01, 0.01, 0.008,
                               self.dark_crease, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.035, 1.11, 0.40), side), (side, -0.35, -0.5), 0.04, 0.008, 0.006,
                               self.dark_crease, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.05, 1.235, 0.322), side), (0.0, 0.0, 1.0), 0.02, 0.028, 0.022,
                               self.dark_crease, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.05, 1.252, 0.338), side), (side, -0.25, 0.0), 0.03, 0.015, 0.012,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.08, 1.20, 0.32), side), (side * 0.3, -0.2, 1.0), 0.04, 0.025, 0.025,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.08, 1.12, 0.30), side), (side * 0.2, -0.4, 1.0), 0.06, 0.035, 0.035,
                               self.skin, scales=self.fine_lumps)
            self.use_bones("jaw")
            sculptor.spike(mirrored((0.04, 1.105, 0.40), side), (0.0, 1.0, 0.2), 0.03, 0.008, self.teeth)
            self.use_bones("head", "jaw")
            sculptor.tube(mirrored_all(((0.115, 1.24, 0.18), (0.19, 1.29, 0.12), (0.27, 1.36, 0.06)), side),
                          ((0.0, 0.015, 0.05), (0.4, 0.013, 0.045), (1.0, 0.004, 0.004)), self.skin, rings=14,
                          segments=14, up_hint=(0.0, 1.0, 0.0), cap_start=False)
            sculptor.ellipsoid(mirrored((0.177, 1.28, 0.15), side), mirrored((0.6, 0.4, -0.45), side), 0.05, 0.006,
                               0.022, self.dark_crease, up_hint=(0.0, 1.0, 0.0))

    def build_mouth_cavity(self):
        self.use_bones("head")
        self.sculptor.ellipsoid((0.0, 1.105, 0.355), (1.0, 0.0, 0.0), 0.055, 0.03, 0.025, self.mouth_cavity, mottle=0.0)

    def build_eyes(self):
        for side in (1.0, -1.0):
            self.sculptor.ellipsoid(mirrored((0.05, 1.237, 0.34), side), (side, 0.15, 0.0), 0.016, 0.01, 0.009,
                                    self.eye_color, mottle=0.0)

    def build_arm(self, side):
        sculptor = self.sculptor
        sculptor.tube(mirrored_all(self.upper_arm_points, side),
                      ((0.0, 0.11, 0.11), (0.5, 0.095, 0.095), (1.0, 0.08, 0.08)), self.skin, rings=16, segments=24,
                      up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)
        arm_axis = mirrored((0.12, -0.29, 0.01), side)
        sculptor.ellipsoid(mirrored((0.40, 0.86, 0.11), side), arm_axis, 0.12, 0.07, 0.065, self.skin,
                           up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)
        sculptor.ellipsoid(mirrored((0.43, 0.85, -0.01), side), arm_axis, 0.13, 0.07, 0.065, self.skin,
                           up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)
        sculptor.ellipsoid(mirrored(self.forearm_points[0], side), (0.0, -1.0, 0.0), 0.085, 0.085, 0.085, self.skin,
                           scales=self.limb_lumps)
        sculptor.tube(mirrored_all(self.forearm_points, side),
                      ((0.0, 0.09, 0.085), (0.35, 0.095, 0.09), (1.0, 0.06, 0.055)), self.skin, rings=18,
                      segments=24, up_hint=(0.0, 1.0, 0.0), scales=self.limb_lumps)
        sculptor.ellipsoid(mirrored((0.44, 0.75, 0.17), side), mirrored((-0.25, 0.1, 1.0), side), 0.12, 0.07,
                           0.07, self.skin, up_hint=(0.0, 1.0, 0.0), scales=self.limb_lumps)

    def build_hand(self, side):
        sculptor = self.sculptor
        axis = numpy.asarray(self.palm_axis) / numpy.linalg.norm(self.palm_axis)
        sculptor.ellipsoid(mirrored(self.palm_center, side), self.palm_axis, 0.08, 0.075, 0.035, self.skin,
                           up_hint=(0.0, 0.0, 1.0), scales=self.fine_lumps)
        palm_end = numpy.asarray(self.palm_center) + axis * 0.07
        for offset, length in zip(self.knuckle_offsets, self.finger_lengths):
            knuckle = palm_end + (offset, 0.0, 0.0)
            middle = knuckle + (offset * 0.15, -0.07 * length, 0.01)
            end_joint = knuckle + (offset * 0.25, -0.13 * length, -0.01)
            tip = knuckle + (offset * 0.3, -0.17 * length, -0.05 * length)
            sculptor.tube(mirrored_all((knuckle, middle, end_joint, tip), side),
                          ((0.0, 0.024, 0.022), (1.0, 0.017, 0.016)), self.skin, rings=14, segments=12)
            for joint, radius in ((knuckle, 0.027), (middle, 0.023), (end_joint, 0.019)):
                sculptor.ellipsoid(mirrored(joint, side), (0.0, -1.0, 0.0), radius, radius, radius * 0.95, self.skin)
            sculptor.spike(mirrored(tip, side), mirrored(tip - end_joint, side), 0.028, 0.014, self.nail)
        thumb = ((0.265, 0.67, 0.54), (0.245, 0.61, 0.58), (0.25, 0.555, 0.585))
        sculptor.tube(mirrored_all(thumb, side), ((0.0, 0.03, 0.03), (1.0, 0.02, 0.02)), self.skin, rings=12,
                      segments=12)
        sculptor.spike(mirrored(thumb[-1], side), (0.0, -1.0, 0.1), 0.026, 0.016, self.nail)

    def build_leg(self, side):
        sculptor = self.sculptor
        sculptor.tube(mirrored_all(self.thigh_points, side),
                      ((0.0, 0.13, 0.13), (0.5, 0.12, 0.115), (1.0, 0.09, 0.09)), self.skin, rings=18, segments=26,
                      up_hint=(0.0, 1.0, 0.0), scales=self.limb_lumps)
        sculptor.ellipsoid(mirrored(self.inward((0.25, 0.61, 0.27))[0], side), (0.0, 0.3, 1.0), 0.09, 0.095, 0.09, self.skin,
                           up_hint=(0.0, 1.0, 0.0), scales=self.limb_lumps)
        sculptor.tube(mirrored_all(self.shin_points, side),
                      ((0.0, 0.085, 0.085), (0.5, 0.075, 0.075), (1.0, 0.06, 0.06)), self.skin, rings=18,
                      segments=22, up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)
        sculptor.ellipsoid(mirrored(self.inward((0.24, 0.40, 0.07))[0], side), (0.0, -1.0, -0.4), 0.15, 0.08, 0.08, self.skin,
                           up_hint=(0.0, 0.0, 1.0), scales=self.limb_lumps)

    def build_foot(self, side):
        sculptor = self.sculptor
        sculptor.ellipsoid(mirrored(self.inward((0.21, 0.075, -0.04))[0], side), (0.0, 0.0, 1.0), 0.075, 0.07, 0.07, self.skin,
                           scales=self.fine_lumps)
        sculptor.ellipsoid(mirrored(self.inward((0.22, 0.065, 0.10))[0], side), (0.0, -0.1, 1.0), 0.16, 0.10, 0.055, self.skin,
                           up_hint=(0.0, 1.0, 0.0), scales=self.fine_lumps)
        for offset, length, radius in zip(self.toe_offsets, self.toe_lengths, self.toe_radii):
            root = numpy.array((0.22 - self.leg_inset + offset, 0.06, 0.20))
            middle = root + (offset * 0.25, -0.005, 0.08 * length)
            tip = root + (offset * 0.45, -0.03, 0.15 * length)
            sculptor.tube(mirrored_all((root, middle, tip), side), ((0.0, radius, radius * 0.9),
                                                                    (1.0, radius * 0.8, radius * 0.7)),
                          self.skin, rings=12, segments=12, up_hint=(0.0, 1.0, 0.0))
            sculptor.ellipsoid(mirrored(middle, side), (0.0, 0.0, 1.0), radius * 1.1, radius * 1.1, radius,
                               self.skin)
            sculptor.ellipsoid(mirrored(tip + (0.0, radius * 0.45, -0.005), side), (0.0, -0.3, 1.0), radius * 0.8,
                               radius * 0.8, radius * 0.3, self.nail, up_hint=(0.0, 1.0, 0.0), mottle=0.02)

    def collided(self, point):
        for center, radius in self.colliders:
            offset = point - center
            distance = float(numpy.linalg.norm(offset))
            if distance < radius:
                point = numpy.asarray(center) + offset / max(distance, 1e-6) * radius
        point[1] = max(point[1], 0.015)
        return point

    def grown_strand(self, root, heading, steps, gravity):
        generator = self.generator
        points = [numpy.asarray(root, dtype=numpy.float64)]
        heading = numpy.asarray(heading, dtype=numpy.float64)
        heading = heading / numpy.linalg.norm(heading)
        fall = numpy.array((0.0, -1.0, -0.3))
        for _ in range(steps):
            heading = heading + fall * gravity + generator.normal(0.0, self.hair_jitter, 3)
            heading = heading / numpy.linalg.norm(heading)
            points.append(self.collided(points[-1] + heading * self.hair_step))
        return numpy.array(points)

    def add_strand(self, points, radius_scale=1.0, root_follows=False):
        generator = self.generator
        centers = catmull_rom(points, len(points) * 2)
        radii = numpy.linspace(self.hair_root_radius, self.hair_tip_radius, len(centers)) * radius_scale
        color = numpy.asarray(self.hair_colors[generator.integers(len(self.hair_colors))]) * generator.uniform(0.85,
                                                                                                             1.1)
        along = numpy.repeat(numpy.linspace(0.0, 1.0, len(centers)), self.hair_segments + 1)
        if root_follows:
            self.mesh.next_weights = 1.0 - self.head_hair_stiffness * along
        self.sculptor.sweep(centers, radii, radii, color, segments=self.hair_segments, mottle=0.0)
        self.hair_along.append(along)
        self.hair_phases.append(numpy.full(len(along), generator.uniform(0.0, 2.0 * math.pi)))

    def scalp_direction(self):
        generator = self.generator
        while True:
            direction = generator.normal(0.0, 1.0, 3)
            direction /= numpy.linalg.norm(direction)
            if direction[1] > 0.05 and direction[2] < 0.45:
                return direction

    def build_hair(self):
        generator = self.generator
        head = numpy.asarray(self.head_center)
        self.use_bones("head")
        for _ in range(self.head_hair_count):
            direction = self.scalp_direction()
            root = head + direction * (0.115, 0.115, 0.13)
            heading = direction + (0.0, 0.3, -0.3)
            self.add_strand(self.grown_strand(root, heading, int(generator.integers(10, 25)), self.hair_gravity),
                            root_follows=True)
        for _ in range(self.wild_hair_count):
            direction = self.scalp_direction()
            root = head + direction * (0.115, 0.115, 0.13)
            heading = direction + (0.0, 1.0, -0.2)
            self.add_strand(self.grown_strand(root, heading, int(generator.integers(3, 7)), 0.04), 0.8)
        for side in (1.0, -1.0):
            self.use_bones(side_name("upper_arm", side), side_name("forearm", side))
            forearm = catmull_rom(mirrored_all(self.forearm_points, side), 12)
            upper_arm = catmull_rom(mirrored_all(self.upper_arm_points, side), 8)
            anchors = numpy.vstack((upper_arm[2:], forearm[:9]))
            for _ in range(self.arm_hair_count):
                anchor = anchors[generator.integers(len(anchors))]
                root = anchor + (side * 0.06, -0.06, -0.03)
                self.add_strand(self.grown_strand(root, (side * 0.3, -1.0, -0.2), int(generator.integers(3, 8)),
                                                  self.hair_gravity), 0.8)
        self.use_bones("pelvis")
        for _ in range(self.hip_hair_count):
            angle = generator.uniform(-0.65, 0.65) * math.pi + math.pi
            root = numpy.array((0.27 * math.sin(angle), 0.52, -0.20 + 0.22 * math.cos(angle)))
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            self.add_strand(self.grown_strand(root, outward + (0.0, -0.8, 0.0), int(generator.integers(6, 12)),
                                              self.hair_gravity))


class Troll:

    def __init__(self, height, model=None):
        self.model = model or TrollModel()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.acting = True
        self.talking = False
        self.speech = Speech()
        self.breaths_per_second = 0.22
        self.breath_fraction = 0.008
        self.hair_sway = 0.03
        self.hair_waves_along = 0.8
        self.breeze_per_second = 0.35
        self.eye_glow = 0.45
        self.skin_specular = (0.10, 0.10, 0.09, 1.0)
        self.skin_shininess = 10.0
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.advance = 0.0
        model = self.model
        self.ground = model.bottom
        self.choreography = Choreography(model.standing_pose, model.stride)
        self.body_skin = Skin(model.body, *model.body_bones, model.skeleton)
        self.eye_skin = Skin(model.eyes, *model.eye_bones, model.skeleton)
        self.hair_skin = Skin(model.hair, *model.hair_bones, model.skeleton)
        self.hair_positions = model.hair[0].copy()
        self.pose()

    def restart(self):
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.pose()

    def update(self, seconds):
        self.seconds += seconds
        if self.acting:
            self.act_seconds += seconds
        self.pose()

    def pose(self):
        self.pose_hair()
        angles, self.advance = self.choreography.pose_at(self.act_seconds) if self.acting else ({}, 0.0)
        if self.talking:
            angles["jaw"] = (self.model.jaw.max_degrees * self.speech.openness(self.seconds), 0.0, 0.0)
        matrices = self.model.skeleton.matrices(angles, (0.0, 0.0, self.advance))
        self.body_skin.deform(matrices)
        self.eye_skin.deform(matrices)
        self.hair_skin.deform(matrices, self.hair_positions)
        self.ground = self.body_skin.lowest() if self.acting else self.model.bottom

    def pose_hair(self):
        model = self.model
        along = model.hair_along
        wave = (self.seconds * self.breeze_per_second * 2.0 * math.pi + model.hair_phases
                - 2.0 * math.pi * self.hair_waves_along * along)
        amount = self.hair_sway * along ** 1.5
        rest = model.hair[0]
        self.hair_positions[:, 0] = rest[:, 0] + amount * numpy.sin(wave)
        self.hair_positions[:, 2] = rest[:, 2] + 0.6 * amount * numpy.cos(wave)

    def breathing_scale(self):
        return 1.0 + self.breath_fraction * math.sin(self.seconds * self.breaths_per_second * 2.0 * math.pi)

    def scale(self):
        return self.height / self.model.total_height

    def focus(self):
        forward = self.advance * self.scale()
        return self.position[0] + forward * math.sin(self.yaw), self.position[2] + forward * math.cos(self.yaw)

    @staticmethod
    def draw(positions, normals, colors, indices):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def begin(self):
        scale = self.scale()
        breathing = self.breathing_scale()
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(math.degrees(self.yaw), 0.0, 1.0, 0.0)
        glScalef(scale * breathing, scale / breathing ** 0.5, scale * breathing)
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

    @staticmethod
    def end():
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()

    def render(self):
        model = self.model
        self.begin()
        self.draw(*self.body_skin.arrays())
        self.draw(*self.hair_skin.arrays())
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (*(numpy.asarray(model.eye_color) * self.eye_glow), 1.0))
        self.draw(*self.eye_skin.arrays())
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
        self.end()
