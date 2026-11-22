import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, catmull_rom, mottling, normalized, surface_normals, \
    unit_or_fallback
from lib.animals.shark import quadratic_curve
from lib.fantasy.anatomy import Jaw, MuscleRelief, Speech, smoothstep
from lib.fantasy.rig import Bone, Choreography, LabeledMesh, Skin, biped_skeleton, both_sides, jaw_bone, mirrored, \
    mirrored_all, side_name


class DemonModel:

    def __init__(self):
        self.configure()
        self.build()

    def configure(self):
        self.skin = (0.60, 0.13, 0.08)
        self.dark_skin = (0.36, 0.07, 0.05)
        self.horn_base = (0.22, 0.14, 0.12)
        self.horn_tip = (0.05, 0.04, 0.04)
        self.spike_color = (0.16, 0.11, 0.10)
        self.claw = (0.09, 0.07, 0.07)
        self.teeth = (0.82, 0.74, 0.56)
        self.membrane = (0.30, 0.07, 0.06)
        self.eye_color = (1.0, 0.80, 0.28)
        self.mouth_color = (1.0, 0.38, 0.08)
        self.torso_points = ((0.0, 0.90, -0.02), (0.0, 1.05, 0.0), (0.0, 1.22, 0.01), (0.0, 1.40, 0.0),
                             (0.0, 1.55, -0.03), (0.0, 1.64, -0.04))
        self.torso_profile = ((0.0, 0.15, 0.105), (0.22, 0.15, 0.10), (0.45, 0.19, 0.115), (0.7, 0.25, 0.13),
                              (0.88, 0.26, 0.12), (1.0, 0.13, 0.09))
        self.torso_relief = MuscleRelief()
        self.horn_points = ((0.05, 1.895, 0.05), (0.12, 1.95, 0.01), (0.20, 1.985, -0.08), (0.26, 2.05, -0.17),
                            (0.27, 2.14, -0.20), (0.24, 2.22, -0.15))
        self.horn_radius = 0.034
        self.horn_ridges = 11
        self.horn_ridge_depth = 0.08
        self.back_horn_points = ((0.06, 1.88, -0.02), (0.10, 1.87, -0.09), (0.13, 1.83, -0.15), (0.14, 1.77, -0.18))
        self.back_horn_radius = 0.018
        self.horns = ((self.horn_points, self.horn_radius, self.horn_ridges, None),
                      (self.back_horn_points, self.back_horn_radius, 6, None))
        self.upper_arm_points = ((0.29, 1.50, -0.01), (0.35, 1.34, -0.03), (0.39, 1.19, -0.04))
        self.forearm_points = ((0.39, 1.19, -0.04), (0.42, 1.07, 0.02), (0.43, 0.95, 0.09))
        self.palm_center = (0.435, 0.89, 0.11)
        self.knuckle_depths = (0.075, 0.10, 0.125, 0.15)
        self.finger_lengths = (0.85, 1.0, 1.0, 0.85)
        self.leg_inset = 0.04
        self.jaw = Jaw(hinge=(0.0, 1.78, 0.0), lip_front=(0.0, 1.746, 0.17), half_width=0.085,
                       chin=(0.0, 1.715, 0.15), max_degrees=22.0)
        self.thigh_points = self.inward((0.11, 0.97, 0.0), (0.135, 0.82, 0.07), (0.145, 0.67, 0.11))
        self.shin_points = self.inward((0.145, 0.67, 0.11), (0.15, 0.55, 0.05), (0.15, 0.44, -0.02))
        self.instep_points = self.inward((0.15, 0.44, -0.02), (0.15, 0.38, 0.0), (0.15, 0.33, 0.04))
        self.tail_points = ((0.0, 0.92, -0.08), (0.0, 0.80, -0.16), (0.06, 0.60, -0.24), (0.20, 0.42, -0.20),
                            (0.30, 0.28, -0.05), (0.26, 0.18, 0.12), (0.12, 0.12, 0.20), (-0.02, 0.12, 0.18))
        self.tail_profile = ((0.0, 0.07, 0.065), (0.3, 0.05, 0.045), (0.7, 0.025, 0.022), (1.0, 0.009, 0.008))
        self.tail_curl_center = (0.12, 0.42, -0.02)
        self.tail_centerline_samples = 64
        self.has_tail = True
        self.wing_scale = 1.0
        self.wing_shoulder = (0.10, 1.52, -0.14)
        self.wing_elbow = (0.50, 1.92, -0.32)
        self.wing_wrist = (1.00, 2.35, -0.34)
        self.wing_flank = (0.12, 1.05, -0.12)
        self.wing_fingers = (((1.45, 2.50, -0.30), (1.85, 2.10, -0.20)),
                             ((1.40, 1.85, -0.30), (1.70, 1.25, -0.20)),
                             ((1.15, 1.30, -0.35), (1.25, 0.55, -0.25)),
                             ((0.80, 1.10, -0.40), (0.65, 0.40, -0.30)))
        self.membrane_rows = 36
        self.membrane_columns = 18
        self.membrane_sag = 0.12
        self.membrane_billow = 0.08
        self.membrane_half_thickness = 0.004
        self.membrane_vein_count = 4
        self.membrane_vein_darkening = 0.35
        self.wing_hinge_start = 0.14
        self.wing_hinge_span = 0.5
        self.wingtip_hinge_start = 0.85
        self.wingtip_hinge_span = 0.6
        self.stride = 0.45
        self.standing_pose = {"tail": (70.0, 0.0, 0.0)}
        both_sides(self.standing_pose, "thigh", 20.0)
        both_sides(self.standing_pose, "shin", -49.5)
        both_sides(self.standing_pose, "foot", 28.0)

    def inward(self, *points):
        return tuple((point[0] - self.leg_inset, point[1], point[2]) for point in points)

    def build_skeleton(self):
        radii = {"pelvis": 0.15, "chest": 0.24, "head": 0.09, "upper_arm": 0.085, "forearm": 0.07, "thigh": 0.08,
                 "shin": 0.05, "foot": 0.04, "hand": 0.05, "waist_blend": 0.10, "neck_blend": 0.06,
                 "shoulder_blend": 0.08, "elbow_blend": 0.05, "wrist_blend": 0.03, "hip_blend": 0.07,
                 "knee_blend": 0.04, "ankle_blend": 0.03}
        tail = Bone("tail", "pelvis", self.tail_points[:3], 0.07, 0.06)
        return biped_skeleton(((0.0, 1.12, 0.0), (0.0, 0.80, -0.02)),
                              ((0.0, 1.12, 0.0), (0.0, 1.40, 0.0), (0.0, 1.62, -0.03)),
                              ((0.0, 1.60, -0.03), (0.0, 1.76, 0.02), (0.0, 1.84, 0.06)),
                              (self.upper_arm_points[0], self.upper_arm_points[-1]),
                              (self.forearm_points[0], self.forearm_points[-1]),
                              (self.forearm_points[-1], (0.42, 0.78, 0.13)),
                              (self.thigh_points[0], self.thigh_points[-1]),
                              (self.shin_points[0], self.shin_points[-1]),
                              (self.instep_points[0], self.instep_points[-1], *self.inward((0.16, 0.27, 0.12))),
                              radii, (tail, jaw_bone(self.jaw, 0.04)))

    def use_bones(self, *names):
        self.mesh.bone_group = names

    def build(self):
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.body, self.body_bones = self.built(self.build_body)
        self.eyes, self.eye_bones = self.built(self.build_eyes, ("head",))
        self.mouth, self.mouth_bones = self.built(self.build_mouth, ("head",))
        self.tail = None
        if self.has_tail:
            self.tail, self.tail_bones = self.built(self.build_tail, ("tail",))
            self.tail_along = self.centerline_fractions(self.tail[0], self.tail_points)
        self.wings, self.wing_bones = self.built(self.build_wings, ("chest",))
        self.prepare_wing_hinges()
        heights = self.body[0][:, 1]
        if self.tail is not None:
            heights = numpy.concatenate((heights, self.tail[0][:, 1]))
        self.bottom = float(heights.min())
        self.top = float(heights.max())
        self.total_height = self.top - self.bottom

    def built(self, builder, group=("chest",)):
        self.mesh = LabeledMesh()
        self.mesh.bone_group = group
        self.sculptor.mesh = self.mesh
        builder()
        arrays = self.mesh.arrays()
        return arrays, self.mesh.bone_labels(self.skeleton, arrays[0])

    def centerline_fractions(self, positions, control_points):
        centerline = catmull_rom(control_points, self.tail_centerline_samples)
        distances = numpy.linalg.norm(positions[:, None, :] - centerline[None, :, :], axis=-1)
        return (distances.argmin(axis=1) / (self.tail_centerline_samples - 1)).astype(numpy.float32)

    def prepare_wing_hinges(self):
        positions = self.wings[0]
        shoulder_reach = self.wing_shoulder[0]
        reach = shoulder_reach + (numpy.abs(positions[:, 0]) - shoulder_reach) / self.wing_scale
        self.wing_sides = numpy.where(positions[:, 0] >= 0.0, 1.0, -1.0).astype(numpy.float32)
        self.wing_weights = smoothstep((reach - self.wing_hinge_start) / self.wing_hinge_span).astype(numpy.float32)
        self.wingtip_weights = smoothstep((reach - self.wingtip_hinge_start)
                                          / self.wingtip_hinge_span).astype(numpy.float32)
        pivots = numpy.zeros((len(positions), 2), dtype=numpy.float32)
        pivots[:, 0] = self.wing_sides * self.wing_shoulder[0]
        pivots[:, 1] = self.wing_shoulder[1]
        self.wing_pivots = pivots
        self.wing_offsets = positions[:, :2] - pivots

    def build_body(self):
        self.use_bones("pelvis", "chest")
        self.build_torso()
        self.use_bones("pelvis", "chest", "upper_arm_r", "upper_arm_l", "thigh_r", "thigh_l")
        self.build_muscles()
        self.use_bones("chest", "head")
        self.build_neck()
        self.use_bones("head", "jaw")
        self.build_head()
        for side in (1.0, -1.0):
            self.use_bones("head")
            self.build_horns(side)
            self.use_bones(side_name("upper_arm", side), side_name("forearm", side))
            self.build_arm(side)
            self.use_bones(side_name("forearm", side), side_name("hand", side))
            self.build_hand(side)
            self.use_bones(side_name("thigh", side), side_name("shin", side), side_name("foot", side))
            self.build_leg(side)

    def build_torso(self):
        torso = self.sculptor.tube(self.torso_points, self.torso_profile, self.skin, up_hint=(0.0, 0.0, 1.0),
                                   mottle=0.05, scales=self.torso_relief)
        centers, sides, ups, widths, heights = torso
        tangents = normalized(numpy.gradient(centers, axis=0))
        for fraction, length in zip(numpy.linspace(0.12, 0.74, 7), numpy.linspace(0.05, 0.09, 7)):
            index = int(fraction * (len(centers) - 1))
            base = centers[index] - ups[index] * heights[index] * 0.85
            self.sculptor.spike(base, -ups[index] + tangents[index] * 0.5, length, 0.018, self.spike_color,
                                curl=tuple(tangents[index] * 0.15))

    def build_muscles(self):
        sculptor = self.sculptor
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.15, 1.32, -0.07), side), (side * -0.35, 1.0, -0.1), 0.17, 0.07, 0.07,
                               self.skin, up_hint=(0.0, 0.0, 1.0))
            sculptor.ellipsoid(mirrored((0.11, 1.61, -0.04), side), (side, -0.4, 0.0), 0.12, 0.06, 0.06, self.skin)
            sculptor.ellipsoid(mirrored((0.28, 1.52, -0.01), side), (side * 0.45, -1.0, 0.05), 0.11, 0.10, 0.095,
                               self.skin, up_hint=(0.0, 0.0, 1.0), rings=20, segments=24)
            for plate in range(3):
                sculptor.spike(mirrored((0.30, 1.60, -0.05 + plate * 0.04), side), (side * 0.8, 0.8, -0.2 + plate * 0.1),
                               0.10 - plate * 0.015, 0.022, self.spike_color, curl=(0.0, 0.0, -0.1))
            sculptor.ellipsoid(mirrored((0.10, 0.94, -0.04), side), (side * 0.2, -1.0, 0.3), 0.09, 0.085, 0.08,
                               self.skin, up_hint=(0.0, 0.0, 1.0))

    def build_neck(self):
        sculptor = self.sculptor
        sculptor.tube(((0.0, 1.56, -0.03), (0.0, 1.66, -0.01), (0.0, 1.76, 0.02)),
                      ((0.0, 0.10, 0.09), (1.0, 0.075, 0.075)), self.skin, rings=14, segments=24,
                      up_hint=(0.0, 0.0, 1.0), cap_start=False, cap_end=False)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.05, 1.66, 0.03), side), (side * 0.45, -1.0, 0.55), 0.08, 0.03, 0.03,
                               self.skin)

    def build_head(self):
        sculptor = self.sculptor
        sculptor.ellipsoid((0.0, 1.835, 0.01), (0.0, 0.25, 1.0), 0.10, 0.08, 0.085, self.skin,
                           up_hint=(0.0, 1.0, 0.0), rings=20, segments=24)
        sculptor.tube(((0.0, 1.81, 0.06), (0.0, 1.795, 0.12), (0.0, 1.78, 0.165)),
                      ((0.0, 0.06, 0.045), (0.6, 0.045, 0.035), (1.0, 0.03, 0.025)), self.skin, rings=16,
                      segments=20, up_hint=(0.0, 1.0, 0.0), cap_start=False)
        sculptor.tube(((0.0, 1.775, 0.02), (0.0, 1.735, 0.09), (0.0, 1.72, 0.145)),
                      ((0.0, 0.065, 0.03), (0.6, 0.045, 0.022), (1.0, 0.028, 0.016)), self.skin, rings=16,
                      segments=20, up_hint=(0.0, 1.0, 0.0), cap_start=False)
        sculptor.ellipsoid((0.0, 1.875, 0.07), (0.0, 1.0, -0.5), 0.05, 0.016, 0.016, self.skin)
        sculptor.spike((0.0, 1.70, 0.13), (0.0, -1.0, 0.25), 0.07, 0.013, self.spike_color)
        for spike in range(4):
            sculptor.spike((0.0, 1.90 - 0.04 * spike, -0.05 - 0.02 * spike), (0.0, 0.5 - 0.3 * spike, -1.0),
                           0.09, 0.016, self.spike_color, curl=(0.0, -0.1, 0.0))
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.042, 1.840, 0.105), side), (side, 0.5, -0.35), 0.05, 0.022, 0.018,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.058, 1.795, 0.075), side), (side * 0.35, -0.15, 1.0), 0.045, 0.02,
                               0.018, self.skin)
            sculptor.spike(mirrored((0.015, 1.80, 0.15), side), (side * 0.3, 1.0, 0.5), 0.025, 0.007,
                           self.spike_color)
            sculptor.spike(mirrored((0.075, 1.83, -0.01), side), (side, 0.35, -0.45), 0.10, 0.025, self.skin)
            sculptor.spike(mirrored((0.07, 1.86, -0.02), side), (side * 0.6, 0.3, -1.0), 0.08, 0.014,
                           self.spike_color)
            sculptor.spike(mirrored((0.03, 1.715, 0.10), side), (side * 0.3, -1.0, 0.1), 0.05, 0.010,
                           self.spike_color)
            sculptor.spike(mirrored((0.06, 1.75, 0.04), side), (side, -0.5, -0.3), 0.06, 0.012, self.spike_color)
            self.use_bones("head")
            sculptor.spike(mirrored((0.022, 1.765, 0.15), side), (0.0, -1.0, 0.15), 0.05, 0.008, self.teeth)
            for depth, length in ((0.125, 0.025), (0.095, 0.02)):
                sculptor.spike(mirrored((0.036, 1.768, depth), side), (0.0, -1.0, 0.05), length, 0.006, self.teeth)
            self.use_bones("jaw")
            sculptor.spike(mirrored((0.03, 1.735, 0.13), side), (0.0, 1.0, 0.1), 0.035, 0.007, self.teeth)
            self.use_bones("head", "jaw")

    def build_eyes(self):
        for side in (1.0, -1.0):
            self.sculptor.ellipsoid(mirrored((0.037, 1.818, 0.112), side), (side, 0.4, -0.25), 0.022, 0.007, 0.010,
                                    self.eye_color, mottle=0.0)

    def build_mouth(self):
        self.sculptor.ellipsoid((0.0, 1.752, 0.10), (0.0, -0.2, 1.0), 0.055, 0.035, 0.014, self.mouth_color,
                                up_hint=(0.0, 1.0, 0.0), mottle=0.0)

    def ridged_horn(self, points, radius, ridges, side, up_hint=None):
        rings = 64
        centers = catmull_rom(mirrored_all(points, side), rings)
        along = numpy.linspace(0.0, 1.0, rings)
        radii = radius * (1.0 - along) ** 0.85 * (1.0 + self.horn_ridge_depth * numpy.sin(along * ridges * 2.0
                                                                                         * math.pi)) + 0.001
        shading = along[:, None, None]
        colors = (numpy.asarray(self.horn_base) * (1.0 - shading) + numpy.asarray(self.horn_tip) * shading)
        self.sculptor.sweep(centers, radii, radii * 0.92, colors, up_hint=up_hint, segments=18, mottle=0.04)

    def build_horns(self, side):
        for points, radius, ridges, up_hint in self.horns:
            self.ridged_horn(points, radius, ridges, side, up_hint)

    def build_arm(self, side):
        sculptor = self.sculptor
        sculptor.tube(mirrored_all(self.upper_arm_points, side),
                      ((0.0, 0.085, 0.085), (0.5, 0.075, 0.075), (1.0, 0.065, 0.065)), self.skin, rings=18,
                      segments=24, up_hint=(0.0, 0.0, 1.0))
        arm_axis = (side * 0.35, -1.0, -0.1)
        sculptor.ellipsoid(mirrored((0.35, 1.34, 0.025), side), arm_axis, 0.10, 0.055, 0.05, self.skin,
                           up_hint=(0.0, 0.0, 1.0))
        sculptor.ellipsoid(mirrored((0.37, 1.36, -0.07), side), arm_axis, 0.11, 0.055, 0.05, self.skin,
                           up_hint=(0.0, 0.0, 1.0))
        sculptor.ellipsoid(mirrored(self.forearm_points[0], side), (0.0, -1.0, 0.2), 0.065, 0.065, 0.065,
                           self.skin)
        sculptor.tube(mirrored_all(self.forearm_points, side),
                      ((0.0, 0.075, 0.07), (0.35, 0.075, 0.07), (1.0, 0.048, 0.042)), self.skin, rings=18,
                      segments=24, up_hint=(0.0, 0.0, 1.0))
        sculptor.ellipsoid(mirrored((0.41, 1.12, 0.0), side), (side * 0.2, -1.0, 0.4), 0.08, 0.06, 0.055,
                           self.skin, up_hint=(0.0, 0.0, 1.0))
        sculptor.spike(mirrored((0.39, 1.18, -0.09), side), mirrored((0.25, -0.4, -1.0), side), 0.13, 0.025,
                       self.spike_color, curl=(0.0, 0.2, 0.0))
        forearm = catmull_rom(self.forearm_points, 9)
        for index, length in ((2, 0.08), (4, 0.065), (6, 0.05)):
            base = forearm[index] + (0.055, 0.0, -0.01)
            sculptor.spike(mirrored(base, side), mirrored((1.0, 0.3, -0.6), side), length, 0.016, self.spike_color)

    def build_hand(self, side):
        sculptor = self.sculptor
        sculptor.ellipsoid(mirrored(self.palm_center, side), (0.0, -1.0, 0.35), 0.055, 0.048, 0.03, self.skin)
        for knuckle_depth, length in zip(self.knuckle_depths, self.finger_lengths):
            root = numpy.array((0.435, 0.855, knuckle_depth))
            joint = root + (-0.012, -0.05 * length, 0.012)
            tip = root + (-0.04, -0.085 * length, 0.004)
            sculptor.tube(mirrored_all((root, joint, tip), side), ((0.0, 0.017, 0.017), (1.0, 0.011, 0.011)),
                          self.skin, rings=10, segments=12)
            sculptor.spike(mirrored(tip, side), mirrored((-0.75, -0.6, 0.1), side), 0.065, 0.011, self.claw,
                           curl=tuple(mirrored((-0.12, 0.0, 0.0), side)))
        thumb = ((0.42, 0.88, 0.155), (0.40, 0.85, 0.18), (0.38, 0.83, 0.185))
        sculptor.tube(mirrored_all(thumb, side), ((0.0, 0.02, 0.02), (1.0, 0.012, 0.012)), self.skin, rings=10,
                      segments=12)
        sculptor.spike(mirrored(thumb[-1], side), mirrored((-0.6, -0.6, 0.3), side), 0.055, 0.012, self.claw,
                       curl=tuple(mirrored((-0.1, 0.0, 0.0), side)))

    def build_leg(self, side):
        sculptor = self.sculptor
        sculptor.tube(mirrored_all(self.thigh_points, side),
                      ((0.0, 0.085, 0.085), (0.5, 0.075, 0.075), (1.0, 0.055, 0.055)), self.skin, rings=16,
                      segments=22, up_hint=(0.0, 0.0, 1.0))
        knee = self.thigh_points[-1]
        sculptor.ellipsoid(mirrored((knee[0], knee[1], knee[2] + 0.01), side), (0.0, -1.0, 0.2), 0.05, 0.05,
                           0.045, self.skin, up_hint=(0.0, 0.0, 1.0))
        sculptor.spike(mirrored((knee[0], knee[1], knee[2] + 0.05), side), mirrored((0.2, 0.3, 1.0), side), 0.07,
                       0.016, self.spike_color, curl=(0.0, 0.15, 0.0))
        sculptor.tube(mirrored_all(self.shin_points, side),
                      ((0.0, 0.052, 0.05), (0.4, 0.05, 0.048), (1.0, 0.032, 0.03)), self.skin, rings=14,
                      segments=20, up_hint=(0.0, 0.0, 1.0))
        sculptor.ellipsoid(mirrored(self.inward((0.15, 0.57, 0.005))[0], side), (0.0, -1.0, 0.45), 0.07, 0.045, 0.045, self.skin,
                           up_hint=(0.0, 0.0, 1.0))
        sculptor.tube(mirrored_all(self.instep_points, side), ((0.0, 0.032, 0.03), (1.0, 0.03, 0.025)),
                      self.skin, rings=10, segments=16, up_hint=(0.0, 0.0, 1.0))
        ankle = self.instep_points[0]
        sculptor.spike(mirrored((ankle[0], ankle[1], ankle[2] - 0.025), side), (0.0, -0.2, -1.0), 0.06, 0.014,
                       self.spike_color)
        sculptor.ellipsoid(mirrored(self.inward((0.15, 0.33, 0.06))[0], side), (0.0, -0.6, 1.0), 0.04, 0.035, 0.022, self.skin,
                           up_hint=(0.0, 1.0, 0.0))
        for spread in (-1.0, 0.0, 1.0):
            root = numpy.array((0.15 - self.leg_inset + spread * 0.022, 0.325, 0.075))
            joint = root + (spread * 0.008, -0.025, 0.02)
            tip = root + (spread * 0.014, -0.06, 0.03)
            sculptor.tube(mirrored_all((root, joint, tip), side), ((0.0, 0.012, 0.012), (1.0, 0.009, 0.009)),
                          self.skin, rings=8, segments=10)
            sculptor.spike(mirrored(tip, side), mirrored((spread * 0.2, -1.0, 0.35), side), 0.045, 0.009,
                           self.claw, curl=(0.0, 0.0, -0.1))

    def build_tail(self):
        sculptor = self.sculptor
        tail = sculptor.tube(self.tail_points, self.tail_profile, self.skin, rings=72, segments=18,
                             up_hint=(0.0, 0.0, 1.0), cap_start=False, cap_end=False, mottle=0.06)
        centers, _, _, widths, _ = tail
        tangents = normalized(numpy.gradient(centers, axis=0))
        curl_center = numpy.asarray(self.tail_curl_center)
        for fraction in numpy.linspace(0.08, 0.85, 10):
            index = int(fraction * (len(centers) - 1))
            outward = centers[index] - curl_center
            outward = normalized(outward - tangents[index] * numpy.dot(outward, tangents[index]))
            fade = 1.0 - 0.6 * fraction
            sculptor.spike(centers[index] + outward * widths[index] * 0.8, outward - tangents[index] * 0.4,
                           0.07 * fade, 0.016 * fade, self.spike_color)
        tip = centers[-1]
        heading = tangents[-1]
        spade_center = tip + heading * 0.04
        sculptor.ellipsoid(spade_center, heading, 0.06, 0.045, 0.008, self.dark_skin, up_hint=(0.0, 1.0, 0.0))
        across = normalized(numpy.cross(heading, (0.0, 1.0, 0.0)))
        for side in (1.0, -1.0):
            sculptor.spike(spade_center + across * side * 0.035, across * side - heading * 1.2, 0.05, 0.010,
                           self.dark_skin)

    def build_wings(self):
        for side in (1.0, -1.0):
            self.build_wing(side)

    def wing_point(self, point, side):
        shoulder = numpy.asarray(self.wing_shoulder, dtype=numpy.float64)
        return mirrored(shoulder + (numpy.asarray(point, dtype=numpy.float64) - shoulder) * self.wing_scale, side)

    def build_wing(self, side):
        sculptor = self.sculptor
        bone = 0.5 + 0.5 * self.wing_scale
        shoulder, flank = mirrored_all((self.wing_shoulder, self.wing_flank), side)
        elbow, wrist = self.wing_point(self.wing_elbow, side), self.wing_point(self.wing_wrist, side)
        fingers = [quadratic_curve(wrist, self.wing_point(control, side), self.wing_point(tip, side),
                                   self.membrane_rows)
                   for control, tip in self.wing_fingers]
        arm = catmull_rom((wrist, elbow, shoulder, flank), self.membrane_rows)
        edges = fingers + [arm]
        for leading, trailing in zip(edges[:-1], edges[1:]):
            self.add_membrane(wrist, leading, trailing)
        sculptor.ellipsoid((shoulder + elbow) / 2.0 - (0.0, 0.0, 0.02), elbow - shoulder, 0.2 * bone, 0.06 * bone,
                           0.06 * bone, self.skin)
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0 + (0.0, 0.0, -0.02), elbow),
                      ((0.0, 0.05 * bone, 0.05 * bone), (1.0, 0.035 * bone, 0.035 * bone)), self.skin, rings=14,
                      segments=16)
        sculptor.tube((elbow, (elbow + wrist) / 2.0 + (0.0, 0.02, 0.0), wrist),
                      ((0.0, 0.035 * bone, 0.035 * bone), (1.0, 0.028 * bone, 0.028 * bone)), self.skin, rings=14,
                      segments=16)
        sculptor.ellipsoid(elbow, (0.0, 1.0, 0.0), 0.04 * bone, 0.038 * bone, 0.038 * bone, self.skin)
        sculptor.ellipsoid(wrist, (side * 0.3, 1.0, 0.0), 0.034 * bone, 0.03 * bone, 0.03 * bone, self.skin)
        for finger in fingers:
            radii = numpy.linspace(0.022, 0.006, len(finger)) * bone
            sculptor.sweep(finger, radii, radii, self.dark_skin, segments=10, cap_end=True, mottle=0.03)
            sculptor.spike(finger[-1], finger[-1] - finger[-2], 0.05 * bone, 0.007 * bone, self.claw)
        sculptor.spike(wrist, mirrored((-0.15, 1.0, 0.1), side), 0.16 * bone, 0.025 * bone, self.claw,
                       curl=tuple(mirrored((0.1, 0.0, 0.1), side)))
        forearm = catmull_rom((elbow, wrist), 6)
        for point, length in zip(forearm[1:-1], (0.06, 0.07, 0.07, 0.06)):
            sculptor.spike(point + (0.0, 0.025, 0.0), mirrored((-0.4, 1.0, -0.2), side), length * bone,
                           0.012 * bone, self.spike_color)
        sculptor.spike(elbow + (0.0, 0.03, 0.0), mirrored((-0.6, 1.0, -0.3), side), 0.11 * bone, 0.02 * bone,
                       self.spike_color)

    @staticmethod
    def edge_at(edge, along):
        samples = numpy.linspace(0.0, 1.0, len(edge))
        flat = along.ravel()
        points = numpy.stack([numpy.interp(flat, samples, edge[:, axis]) for axis in range(3)], axis=-1)
        return points.reshape(along.shape + (3,))

    def membrane_surface(self, wrist, leading, trailing, along, across):
        points = (self.edge_at(leading, along) * (1.0 - across)[..., None]
                  + self.edge_at(trailing, along) * across[..., None])
        belly = numpy.sin(math.pi * across)
        scallop = 1.0 - self.membrane_sag * belly * along ** 2
        points = wrist + (points - wrist) * scallop[..., None]
        span = numpy.linalg.norm(leading[-1] - trailing[-1])
        billow = self.membrane_billow * span * belly * numpy.sin(math.pi * along * 0.85)
        return points + numpy.array((0.0, 0.0, -1.0)) * billow[..., None]

    def add_membrane(self, wrist, leading, trailing):
        along, across = numpy.meshgrid(numpy.linspace(0.0, 1.0, len(leading)),
                                       numpy.linspace(0.0, 1.0, self.membrane_columns), indexing="ij")
        grid = self.membrane_surface(wrist, leading, trailing, along, across)
        forward = numpy.array((0.0, 0.0, 1.0))
        normals = unit_or_fallback(surface_normals(grid, grid - forward, False), forward)
        belly = numpy.sin(math.pi * across)
        vein_offset = (across * self.membrane_vein_count) % 1.0 - 0.5
        vein = numpy.exp(-vein_offset * vein_offset / 0.004) * along
        brightness = (0.75 + 0.5 * belly * along) * (1.0 - self.membrane_vein_darkening * vein)
        colors = numpy.asarray(self.membrane) * (brightness * mottling(grid, 0.05))[..., None]
        for sign in (1.0, -1.0):
            self.mesh.add_grid(grid + normals * self.membrane_half_thickness * sign, normals * sign, colors)


class RamDemonModel(DemonModel):

    def configure(self):
        super().configure()
        self.skin = (0.68, 0.37, 0.15)
        self.dark_skin = (0.40, 0.19, 0.07)
        self.horn_base = (0.46, 0.40, 0.32)
        self.horn_tip = (0.14, 0.12, 0.10)
        self.spike_color = (0.20, 0.12, 0.07)
        self.membrane = (0.36, 0.17, 0.07)
        self.eye_color = (0.65, 1.0, 0.30)
        self.mouth_color = (0.45, 1.0, 0.25)
        self.ram_horn_center = (1.83, -0.02)
        self.ram_horn_start_angle = 0.8
        self.ram_horn_turns = 0.95
        self.ram_horn_curl_radius = 0.085
        self.ram_horn_tightening = 0.45
        self.ram_horn_inner_reach = 0.06
        self.ram_horn_outward_reach = 0.14
        self.ram_horn_samples = 24
        self.brow_horn_points = ((0.025, 1.895, 0.07), (0.03, 1.95, 0.09), (0.035, 1.99, 0.085))
        self.horns = ((self.ram_horn_points(), 0.042, 16, (1.0, 0.0, 0.0)),
                      (self.brow_horn_points, 0.014, 4, None))
        self.has_tail = False
        self.wing_scale = 0.55

    def ram_horn_points(self):
        center_height, center_depth = self.ram_horn_center
        points = []
        for sample in range(self.ram_horn_samples):
            progress = sample / (self.ram_horn_samples - 1)
            angle = self.ram_horn_start_angle - self.ram_horn_turns * 2.0 * math.pi * progress
            radius = self.ram_horn_curl_radius * (1.0 - self.ram_horn_tightening * progress)
            points.append((self.ram_horn_inner_reach + self.ram_horn_outward_reach * progress ** 0.7,
                           center_height + radius * math.cos(angle), center_depth + radius * math.sin(angle)))
        return points


class Demon:

    def __init__(self, height, model=None):
        self.model = model or DemonModel()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.levitation = 0.0
        self.acting = True
        self.talking = False
        self.speech = Speech()
        self.flapping = True
        self.flaps_per_second = 0.55
        self.flap_degrees = 24.0
        self.acting_flap_degrees = 10.0
        self.wingtip_degrees = 14.0
        self.wingtip_lag = 0.9
        self.flap_phase = 0.0
        self.hover_fraction = 0.035
        self.hover_lag = 0.4
        self.tail_swing = 0.05
        self.tail_waves_along = 1.2
        self.tail_wiggles_per_second = 0.4
        self.tail_phase = 0.0
        self.eye_glow = 1.0
        self.eye_pulse = 0.25
        self.eye_pulses_per_second = 0.7
        self.mouth_glow = 0.75
        self.skin_specular = (0.20, 0.13, 0.11, 1.0)
        self.skin_shininess = 22.0
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.advance = 0.0
        model = self.model
        self.ground = model.bottom
        skeleton = model.skeleton
        self.choreography = Choreography(model.standing_pose, model.stride)
        self.body_skin = Skin(model.body, *model.body_bones, skeleton)
        self.eye_skin = Skin(model.eyes, *model.eye_bones, skeleton)
        self.mouth_skin = Skin(model.mouth, *model.mouth_bones, skeleton)
        self.wing_skin = Skin(model.wings, *model.wing_bones, skeleton)
        self.tail_skin = None if model.tail is None else Skin(model.tail, *model.tail_bones, skeleton)
        self.wing_positions = model.wings[0].copy()
        self.wing_normals = model.wings[1].copy()
        self.tail_positions = None if model.tail is None else model.tail[0].copy()
        self.pose()

    def restart(self):
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.flap_phase = 0.0
        self.tail_phase = 0.0
        self.pose()

    def update(self, seconds):
        self.seconds += seconds
        if self.acting:
            self.act_seconds += seconds
        if self.flapping:
            self.flap_phase = (self.flap_phase + seconds * self.flaps_per_second * 2.0 * math.pi) % (2.0 * math.pi)
        self.tail_phase = (self.tail_phase + seconds * self.tail_wiggles_per_second * 2.0 * math.pi) % (2.0 * math.pi)
        self.pose()

    def pose(self):
        self.pose_wings()
        self.pose_tail()
        angles, self.advance = self.choreography.pose_at(self.act_seconds) if self.acting else ({}, 0.0)
        if self.talking:
            angles["jaw"] = (self.model.jaw.max_degrees * self.speech.openness(self.seconds), 0.0, 0.0)
        matrices = self.model.skeleton.matrices(angles, (0.0, 0.0, self.advance))
        self.body_skin.deform(matrices)
        self.eye_skin.deform(matrices)
        self.mouth_skin.deform(matrices)
        self.wing_skin.deform(matrices, self.wing_positions, self.wing_normals)
        if self.tail_skin is not None:
            self.tail_skin.deform(matrices, self.tail_positions)
        self.ground = self.body_skin.lowest() if self.acting else self.model.bottom

    def pose_wings(self):
        model = self.model
        degrees = self.acting_flap_degrees if self.acting else self.flap_degrees
        flap = math.radians(degrees) * math.sin(self.flap_phase)
        wingtip = math.radians(self.wingtip_degrees) * math.sin(self.flap_phase - self.wingtip_lag)
        angles = model.wing_sides * (flap * model.wing_weights + wingtip * model.wingtip_weights)
        cosines, sines = numpy.cos(angles), numpy.sin(angles)
        offset_x, offset_y = model.wing_offsets[:, 0], model.wing_offsets[:, 1]
        self.wing_positions[:, 0] = model.wing_pivots[:, 0] + offset_x * cosines - offset_y * sines
        self.wing_positions[:, 1] = model.wing_pivots[:, 1] + offset_x * sines + offset_y * cosines
        normal_x, normal_y = model.wings[1][:, 0], model.wings[1][:, 1]
        self.wing_normals[:, 0] = normal_x * cosines - normal_y * sines
        self.wing_normals[:, 1] = normal_x * sines + normal_y * cosines

    def pose_tail(self):
        if self.tail_positions is None:
            return
        along = self.model.tail_along
        wave = self.tail_phase - 2.0 * math.pi * self.tail_waves_along * along
        amount = self.tail_swing * along ** 1.5
        rest = self.model.tail[0]
        self.tail_positions[:, 0] = rest[:, 0] + amount * numpy.sin(wave)
        self.tail_positions[:, 2] = rest[:, 2] + 0.5 * amount * numpy.cos(wave)

    def scale(self):
        return self.height / self.model.total_height

    def hover_offset(self):
        if self.acting:
            return 0.0
        return self.levitation - self.hover_fraction * self.height * math.sin(self.flap_phase - self.hover_lag)

    def focus(self):
        forward = self.advance * self.scale()
        return self.position[0] + forward * math.sin(self.yaw), self.position[2] + forward * math.cos(self.yaw)

    @staticmethod
    def draw(positions, normals, colors, indices):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def draw_glowing(self, skin, color, strength):
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (*(numpy.asarray(color) * strength), 1.0))
        self.draw(*skin.arrays())
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

    def eye_strength(self):
        pulse = math.sin(self.seconds * self.eye_pulses_per_second * 2.0 * math.pi)
        return self.eye_glow * (1.0 - self.eye_pulse * 0.5 * (1.0 - pulse))

    def begin(self):
        scale = self.scale()
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1] + self.hover_offset(), self.position[2])
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
        if self.tail_skin is not None:
            self.draw(*self.tail_skin.arrays())
        self.draw(*self.wing_skin.arrays())
        self.draw_glowing(self.eye_skin, model.eye_color, self.eye_strength())
        self.draw_glowing(self.mouth_skin, model.mouth_color, self.mouth_glow)
        self.end()
