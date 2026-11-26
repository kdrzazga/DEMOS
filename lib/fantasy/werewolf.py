import math

import numpy

from lib.animals.dragon import Sculptor, catmull_rom, mottling, normalized
from lib.fantasy.anatomy import Jaw, MuscleRelief, Speech, smoothstep
from lib.fantasy.rig import Choreography, LabeledMesh, mirrored, side_name, sided
from lib.fantasy.sorcerer import RobeFolds
from lib.fantasy.vampire import Vampire, VampireModel


class ClawLunge(Choreography):

    def strike_hold_seconds(self):
        return 0.6

    def guard(self):
        pose = {"chest": (12.0, 0.0, 0.0), "head": (-6.0, 0.0, 0.0)}
        for side in (1.0, -1.0):
            sided(pose, "upper_arm", side, -45.0, 0.0, 35.0)
            sided(pose, "forearm", side, -60.0)
            sided(pose, "hand", side, -25.0)
        sided(pose, "thigh", -1.0, -26.0)
        sided(pose, "shin", -1.0, 30.0)
        sided(pose, "foot", -1.0, -4.0)
        sided(pose, "thigh", 1.0, 14.0)
        sided(pose, "shin", 1.0, 18.0)
        sided(pose, "foot", 1.0, -10.0)
        return pose

    def punch(self):
        pose = {"chest": (26.0, 0.0, 0.0), "head": (-24.0, 0.0, 0.0), "bite": (1.0, 0.0, 0.0)}
        for side in (1.0, -1.0):
            sided(pose, "upper_arm", side, -85.0, 0.0, 18.0)
            sided(pose, "forearm", side, -12.0)
            sided(pose, "hand", side, -35.0)
        sided(pose, "thigh", -1.0, -42.0)
        sided(pose, "shin", -1.0, 44.0)
        sided(pose, "foot", -1.0, -4.0)
        sided(pose, "thigh", 1.0, 26.0)
        sided(pose, "shin", 1.0, 12.0)
        sided(pose, "foot", 1.0, -16.0)
        return pose


class WerewolfModel(VampireModel):

    def __init__(self, seed=41):
        self.generator = numpy.random.default_rng(seed)
        self.skin = (0.25, 0.26, 0.29)
        self.ear_inside = (0.30, 0.22, 0.25)
        self.fur_dark = (0.07, 0.07, 0.09)
        self.fur_mid = (0.24, 0.25, 0.29)
        self.fur_light = (0.55, 0.57, 0.62)
        self.muzzle = (0.36, 0.37, 0.41)
        self.nose = (0.04, 0.035, 0.045)
        self.lip = (0.06, 0.04, 0.05)
        self.gum = (0.30, 0.06, 0.08)
        self.mouth_inside = (0.32, 0.03, 0.05)
        self.tongue = (0.62, 0.14, 0.18)
        self.teeth = (0.90, 0.86, 0.68)
        self.claw = (0.06, 0.055, 0.06)
        self.eye_color = (0.72, 1.0, 0.42)
        self.coat = (0.15, 0.38, 0.24)
        self.coat_dark = (0.05, 0.17, 0.14)
        self.coat_light = (0.33, 0.58, 0.34)
        self.coat_lining = (0.05, 0.12, 0.10)
        self.rags = (0.07, 0.07, 0.085)
        self.torso_points = ((0.0, 0.90, -0.02), (0.0, 1.05, 0.0), (0.0, 1.22, 0.01), (0.0, 1.40, 0.0),
                             (0.0, 1.55, -0.03), (0.0, 1.64, -0.04))
        self.torso_profile = ((0.0, 0.15, 0.105), (0.22, 0.15, 0.10), (0.45, 0.18, 0.115), (0.7, 0.225, 0.13),
                              (0.88, 0.235, 0.12), (1.0, 0.13, 0.09))
        self.torso_relief = MuscleRelief()
        self.skull_center = (0.0, 1.80, 0.0)
        self.skull_radii = (0.085, 0.08, 0.10)
        self.snout_points = ((0.0, 1.80, 0.06), (0.0, 1.776, 0.16), (0.0, 1.757, 0.25))
        self.snout_profile = ((0.0, 0.062, 0.052), (0.5, 0.042, 0.036), (1.0, 0.028, 0.026))
        self.lower_jaw_points = ((0.0, 1.737, 0.02), (0.0, 1.716, 0.15), (0.0, 1.718, 0.235))
        self.lower_jaw_profile = ((0.0, 0.05, 0.03), (0.5, 0.034, 0.022), (1.0, 0.021, 0.015))
        self.jaw = Jaw(hinge=(0.0, 1.765, 0.01), lip_front=(0.0, 1.738, 0.25), half_width=0.065,
                       chin=(0.0, 1.70, 0.22), max_degrees=20.0)
        self.eye_center = (0.042, 1.812, 0.088)
        self.ear_base = (0.055, 1.855, -0.02)
        self.ear_tip = (0.115, 2.0, -0.055)
        self.ear_facing = (0.35, 0.1, 1.0)
        self.ear_width = 0.036
        self.ear_cup = 0.012
        self.ear_thickness = 0.0035
        self.ear_rows = 16
        self.ear_columns = 13
        self.shoulders = {1.0: (0.25, 1.52, -0.03), -1.0: (-0.25, 1.52, -0.03)}
        self.elbows = {1.0: (0.31, 1.21, -0.03), -1.0: (-0.31, 1.21, -0.03)}
        self.wrists = {1.0: (0.34, 0.90, 0.04), -1.0: (-0.34, 0.90, 0.04)}
        self.hand_directions = {1.0: (0.05, -1.0, 0.15), -1.0: (-0.05, -1.0, 0.15)}
        self.palm_normals = {1.0: (-1.0, 0.0, 0.0), -1.0: (1.0, 0.0, 0.0)}
        self.finger_curls = {1.0: 38.0, -1.0: 38.0}
        self.finger_spreads = {1.0: 0.7, -1.0: 0.7}
        self.thumb_sides = {1.0: -1.0, -1.0: 1.0}
        self.hand_size = 1.45
        self.hips = (0.11, 0.98, 0.0)
        self.knees = (0.12, 0.53, 0.05)
        self.ankles = (0.11, 0.11, 0.0)
        self.toes = (0.12, 0.02, 0.30)
        self.cape_center_z = -0.01
        self.coat_radii = ((1.62, 0.12, 0.10), (1.56, 0.25, 0.16), (1.48, 0.27, 0.17), (1.30, 0.25, 0.16),
                           (1.05, 0.23, 0.165), (0.90, 0.26, 0.19), (0.60, 0.31, 0.23), (0.25, 0.35, 0.27))
        self.coat_wrap = math.pi - 0.55
        self.coat_hem = 0.28
        self.coat_tatter = 0.2
        self.coat_rows = 60
        self.coat_columns = 121
        self.coat_folds = 11.0
        self.coat_fold_depth = (0.004, 0.025)
        self.coat_leg_start = 1.0
        self.coat_leg_fade = 0.3
        self.coat_leg_share = 0.8
        self.coat_front_blend = 0.14
        self.sleeve_folds = RobeFolds(7, 0.004, 0.012, 0.07, 0.75, 9, 26, 48)
        self.trouser_folds = RobeFolds(8, 0.003, 0.01, 0.09, 0.7, 11, 28, 40)
        self.tuft_rings = 5
        self.tuft_segments = 4
        self.head_fur = 170
        self.mane_fur = 190
        self.chest_fur = 55
        self.arm_fur = 55
        self.thigh_fur = 30
        self.shin_fur = 75
        self.stride = 0.55
        self.punching_side = 1.0
        self.standing_pose = {}
        self.seat_drop = 0.09
        self.seat_reach = 0.36
        self.back_contact = -0.22
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.cloth, self.cloth_bones = self.built(self.build_cloth)
        self.attach_coat_to_legs()
        self.body, self.body_bones = self.built(self.build_body)
        self.eyes, self.eye_bones = self.built(self.build_eyes, ("head",))
        self.cloth_looseness = self.looseness(self.cloth[0])
        heights = numpy.concatenate([part[0][:, 1] for part in (self.cloth, self.body)])
        self.bottom = float(heights.min())
        self.total_height = float(heights.max()) - self.bottom

    @staticmethod
    def looseness(positions):
        return (numpy.clip((1.0 - positions[:, 1]) / 0.75, 0.0, 1.0) ** 1.4).astype(numpy.float32)

    def build_cloth(self):
        self.use_bones("pelvis", "chest")
        self.build_coat()
        self.use_bones("chest")
        self.build_coat_collar()

    def build_coat(self):
        generator = self.generator
        angle = numpy.linspace(-self.coat_wrap, self.coat_wrap, self.coat_columns)[None, :]
        shreds = numpy.abs(numpy.sin(angle * 13.0 + 3.0 * numpy.sin(angle * 5.0))) ** 0.5
        hem = self.coat_hem + self.coat_tatter * (1.0 - shreds) * generator.uniform(0.4, 1.0, angle.shape)
        top = self.coat_radii[0][0]
        drop = numpy.linspace(0.0, 1.0, self.coat_rows)[:, None]
        heights = top - (top - hem) * drop
        levels, widths, depths = (numpy.array(column)[::-1] for column in zip(*self.coat_radii))
        radius_x = numpy.interp(heights, levels, widths)
        radius_z = numpy.interp(heights, levels, depths)
        wave = numpy.sin(angle * self.coat_folds + 0.7 * numpy.sin(angle * 3.0 + 1.0))
        shallow, deep = self.coat_fold_depth
        fold = wave * (shallow + (deep - shallow) * drop ** 1.2)
        grid = numpy.stack(((radius_x + fold) * numpy.sin(angle), heights,
                            self.cape_center_z - (radius_z + fold) * numpy.cos(angle)), axis=-1)
        streaks = 0.5 + 0.5 * numpy.sin(grid[..., 0] * 23.0 + grid[..., 1] * 9.0 + 2.0 * numpy.sin(grid[..., 1] * 31.0))
        dark, light = numpy.asarray(self.coat_dark), numpy.asarray(self.coat_light)
        base = numpy.asarray(self.coat)
        tint = numpy.where(streaks[..., None] > 0.5, base + (light - base) * (streaks[..., None] - 0.5),
                           dark + (base - dark) * streaks[..., None] * 2.0)
        grime = 1.0 - 0.45 * smoothstep((0.7 - heights) / 0.4)
        shade = (1.0 - 0.3 * (0.5 - 0.5 * wave)) * grime * mottling(grid, 0.08)
        outer = tint * shade[..., None]
        inner = numpy.asarray(self.coat_lining) * shade[..., None]
        self.double_sheet(grid, outer, inner, 0.004)

    def build_coat_collar(self):
        rise = numpy.linspace(0.0, 1.0, 6)[:, None]
        angle = numpy.linspace(-2.2, 2.2, 41)[None, :]
        radius_x = 0.125 + 0.05 * rise
        radius_z = 0.105 + 0.045 * rise
        grid = numpy.stack((radius_x * numpy.sin(angle), 1.60 + 0.075 * rise - 0.02 * rise * numpy.abs(angle),
                            self.cape_center_z - radius_z * numpy.cos(angle)), axis=-1)
        color = numpy.asarray(self.coat) * mottling(grid, 0.08)[..., None]
        self.double_sheet(grid, color, numpy.asarray(self.coat_lining) * numpy.ones_like(grid), 0.004)

    def attach_coat_to_legs(self):
        labels, overrides, _ = self.cloth_bones
        positions = self.cloth[0].astype(numpy.float64)
        hanging = numpy.nonzero(positions[:, 1] < self.coat_leg_start)[0]
        lateral = positions[hanging, 0]
        front = smoothstep((positions[hanging, 2] - self.cape_center_z) / self.coat_front_blend)
        right, left = self.skeleton.index["thigh_r"], self.skeleton.index["thigh_l"]
        labels[hanging] = numpy.where(lateral >= 0.0, right, left)
        overrides[hanging] = (self.coat_leg_share * front
                              * smoothstep((self.coat_leg_start - positions[hanging, 1]) / self.coat_leg_fade))

    def surface_since(self, chunk):
        return (numpy.concatenate(self.mesh.positions[chunk:]).astype(numpy.float64),
                numpy.concatenate(self.mesh.normals[chunk:]).astype(numpy.float64))

    def tuft(self, root, direction, length, radius, droop):
        bent = normalized(direction + numpy.array((0.0, -droop, 0.0)))
        points = (root, root + direction * length * 0.45, root + bent * length)
        centers = catmull_rom(points, self.tuft_rings)
        along = numpy.linspace(0.0, 1.0, self.tuft_rings)
        radii = radius * (1.0 - along) ** 0.9 + 0.0006
        shade = self.generator.uniform(0.0, 1.0)
        root_color = numpy.asarray(self.fur_dark) + (numpy.asarray(self.fur_mid) - numpy.asarray(self.fur_dark)) * shade
        tip_color = numpy.asarray(self.fur_mid) + (numpy.asarray(self.fur_light) - numpy.asarray(self.fur_mid)) * shade
        colors = root_color + (tip_color - root_color) * along[:, None, None]
        self.sculptor.sweep(centers, radii, radii * 0.55, colors, segments=self.tuft_segments, mottle=0.0)

    def grow_fur(self, chunk, count, flow, length, radius, droop, keep=None):
        generator = self.generator
        positions, normals = self.surface_since(chunk)
        normals = normalized(normals)
        candidates = numpy.arange(len(positions)) if keep is None else numpy.nonzero(keep(positions, normals))[0]
        if len(candidates) == 0:
            return
        flow = numpy.asarray(flow, dtype=numpy.float64)
        for index in generator.choice(candidates, size=count):
            normal = normals[index]
            direction = normalized(normal * generator.uniform(0.3, 0.7) + flow + generator.normal(0.0, 0.25, 3))
            self.tuft(positions[index] - normal * 0.004, direction, generator.uniform(*length),
                      generator.uniform(*radius), droop)

    def build_body(self):
        self.use_bones("pelvis", "chest")
        chunk = len(self.mesh.positions)
        self.build_torso()
        self.grow_fur(chunk, self.chest_fur, (0.0, -1.0, 0.1), (0.018, 0.035), (0.004, 0.007), 0.2,
                      lambda points, normals: (points[:, 1] > 1.22) & (points[:, 1] < 1.52) & (normals[:, 2] > 0.4))
        chunk = len(self.mesh.positions)
        self.use_bones("chest", "head")
        self.sculptor.tube(((0.0, 1.50, -0.06), (0.0, 1.64, -0.03), (0.0, 1.76, 0.0)),
                           ((0.0, 0.11, 0.10), (1.0, 0.075, 0.075)), self.fur_mid, rings=14, segments=24,
                           up_hint=(0.0, 0.0, 1.0), cap_start=False, cap_end=False, mottle=0.1)
        self.use_bones("chest")
        self.grow_fur(chunk, self.mane_fur, (0.0, -0.8, -0.5), (0.06, 0.12), (0.008, 0.013), 0.35)
        self.use_bones("head", "jaw")
        self.build_head()
        for side in (1.0, -1.0):
            self.build_arm(side)
            self.use_bones(side_name("hand", side))
            self.build_hand(side)
            self.build_leg(side)

    def build_torso(self):
        sculptor = self.sculptor
        sculptor.tube(self.torso_points, self.torso_profile, self.fur_mid, up_hint=(0.0, 0.0, 1.0),
                      cap_start=False, mottle=0.08, scales=self.torso_relief)
        self.use_bones("pelvis")
        sculptor.ellipsoid((0.0, 0.95, -0.01), (0.0, 1.0, 0.0), 0.06, 0.18, 0.12, self.rags,
                           up_hint=(0.0, 0.0, 1.0), mottle=0.05)
        self.use_bones("pelvis", "chest", "upper_arm_r", "upper_arm_l")
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.12, 1.60, -0.05), side), (side, -0.35, 0.0), 0.12, 0.06, 0.06,
                               self.fur_mid, mottle=0.08)
            sculptor.ellipsoid(mirrored((0.26, 1.51, -0.03), side), (side * 0.4, -1.0, 0.05), 0.10, 0.08, 0.08,
                               self.fur_mid, up_hint=(0.0, 0.0, 1.0), mottle=0.08)
            sculptor.ellipsoid(mirrored((0.14, 1.30, -0.08), side), (side * -0.3, 1.0, -0.1), 0.17, 0.07, 0.07,
                               self.fur_mid, up_hint=(0.0, 0.0, 1.0), mottle=0.08)

    def build_head(self):
        sculptor = self.sculptor
        chunk = len(self.mesh.positions)
        self.use_bones("head")
        sculptor.ellipsoid(self.skull_center, (0.0, 0.1, 1.0), self.skull_radii[2], self.skull_radii[0],
                           self.skull_radii[1], self.fur_mid, up_hint=(0.0, 1.0, 0.0), rings=20, segments=24,
                           mottle=0.1)
        sculptor.tube(self.snout_points, self.snout_profile, self.muzzle, rings=20, segments=22,
                      up_hint=(0.0, 1.0, 0.0), cap_start=False, mottle=0.1)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.04, 1.832, 0.085), side), (side, 0.25, 0.4), 0.04, 0.016, 0.014,
                               self.fur_dark, mottle=0.08)
            sculptor.ellipsoid(mirrored((0.07, 1.775, 0.04), side), (side * 0.5, -0.4, 1.0), 0.06, 0.04, 0.035,
                               self.fur_mid, mottle=0.1)
            sculptor.ellipsoid(mirrored((0.03, 1.80, 0.17), side), (0.0, -0.3, 1.0), 0.05, 0.012, 0.01,
                               self.fur_dark, mottle=0.05)
            self.build_ear(side)
        sculptor.ellipsoid((0.0, 1.768, 0.262), (0.0, 0.2, 1.0), 0.018, 0.024, 0.018, self.nose, mottle=0.03)
        self.grow_fur(chunk, self.head_fur, (0.0, 0.0, -1.0), (0.03, 0.065), (0.006, 0.01), 0.25,
                      lambda points, normals: (points[:, 2] < 0.13) & (normals[:, 1] > -0.5)
                      & (numpy.abs(points[:, 0]) < 0.11))
        self.build_mouth()

    def build_mouth(self):
        sculptor = self.sculptor
        generator = self.generator
        self.use_bones("head", "jaw")
        sculptor.ellipsoid((0.0, 1.742, 0.12), (0.0, 0.0, 1.0), 0.12, 0.034, 0.022, self.mouth_inside,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.0)
        self.use_bones("jaw")
        chunk = len(self.mesh.positions)
        sculptor.tube(self.lower_jaw_points, self.lower_jaw_profile, self.muzzle, rings=18, segments=20,
                      up_hint=(0.0, 1.0, 0.0), cap_start=False, mottle=0.1)
        self.grow_fur(chunk, 26, (0.0, -1.0, -0.4), (0.02, 0.04), (0.004, 0.007), 0.3,
                      lambda points, normals: (normals[:, 1] < -0.3) & (points[:, 2] < 0.2))
        sculptor.ellipsoid((0.0, 1.728, 0.13), (0.0, 0.0, 1.0), 0.09, 0.024, 0.008, self.tongue,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.03)
        for side in (1.0, -1.0):
            self.use_bones("head")
            gum = [mirrored((0.028, self.jaw.mouth_line_height(depth) + 0.004, depth), side)
                   for depth in (0.05, 0.15, 0.245)]
            centers = catmull_rom(gum, 16)
            sculptor.sweep(centers, numpy.full(16, 0.006), numpy.full(16, 0.007), self.lip, up_hint=(0.0, 1.0, 0.0),
                           segments=8, mottle=0.0)
            sculptor.spike(mirrored((0.022, self.jaw.mouth_line_height(0.225), 0.225), side), (0.0, -1.0, 0.1),
                           0.045, 0.009, self.teeth, curl=(0.0, 0.0, -0.05))
            for depth in numpy.linspace(0.08, 0.2, 5):
                sculptor.spike(mirrored((0.026, self.jaw.mouth_line_height(depth), depth), side),
                               (generator.uniform(-0.1, 0.1), -1.0, 0.05), generator.uniform(0.012, 0.02), 0.005,
                               self.teeth)
            self.use_bones("jaw")
            lower = [mirrored((0.024, self.jaw.mouth_line_height(depth) - 0.012, depth), side)
                     for depth in (0.05, 0.15, 0.235)]
            centers = catmull_rom(lower, 16)
            sculptor.sweep(centers, numpy.full(16, 0.005), numpy.full(16, 0.006), self.gum, up_hint=(0.0, 1.0, 0.0),
                           segments=8, mottle=0.0)
            sculptor.spike(mirrored((0.019, self.jaw.mouth_line_height(0.21) - 0.01, 0.21), side), (0.0, 1.0, 0.1),
                           0.04, 0.008, self.teeth, curl=(0.0, 0.0, 0.05))
            for depth in numpy.linspace(0.07, 0.18, 4):
                sculptor.spike(mirrored((0.022, self.jaw.mouth_line_height(depth) - 0.01, depth), side),
                               (0.0, 1.0, 0.05), generator.uniform(0.01, 0.017), 0.005, self.teeth)
        self.use_bones("head", "jaw")

    def build_eyes(self):
        for side in (1.0, -1.0):
            self.sculptor.ellipsoid(mirrored(self.eye_center, side), (side, 0.35, 0.55), 0.017, 0.007, 0.008,
                                    self.eye_color, mottle=0.0)

    def build_arm(self, side):
        sculptor = self.sculptor
        shoulder, elbow, wrist = (numpy.asarray(point) for point in
                                  (self.shoulders[side], self.elbows[side], self.wrists[side]))
        self.use_bones(side_name("upper_arm", side))
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0, elbow), ((0.0, 0.085, 0.085), (1.0, 0.065, 0.065)),
                      self.fur_mid, rings=16, segments=22, mottle=0.08)
        sculptor.tube((shoulder + (0.0, 0.03, 0.0), (shoulder + elbow) / 2.0, elbow),
                      ((0.0, 0.11, 0.105), (1.0, 0.095, 0.09)), self.coat, rings=18, segments=28,
                      cap_start=True, cap_end=False, mottle=0.1, scales=self.sleeve_folds)
        self.use_bones(side_name("forearm", side))
        chunk = len(self.mesh.positions)
        sculptor.tube((elbow, (elbow + wrist) / 2.0, wrist), ((0.0, 0.068, 0.065), (0.4, 0.07, 0.066),
                                                             (1.0, 0.05, 0.046)), self.fur_mid, rings=16,
                      segments=22, mottle=0.08)
        self.grow_fur(chunk, self.arm_fur, (0.0, -1.0, 0.0), (0.025, 0.05), (0.005, 0.009), 0.2,
                      lambda points, normals: points[:, 1] < elbow[1] - 0.08)
        cuff = elbow + (wrist - elbow) * 0.4
        sculptor.tube((elbow, (elbow + cuff) / 2.0, cuff), ((0.0, 0.095, 0.09), (1.0, 0.105, 0.1)), self.coat,
                      rings=14, segments=28, cap_start=False, cap_end=False, mottle=0.1, scales=self.sleeve_folds)

    def build_hand(self, side):
        sculptor = self.sculptor
        size = self.hand_size
        wrist = numpy.asarray(self.wrists[side], dtype=numpy.float64)
        direction = normalized(self.hand_directions[side])
        palm = numpy.asarray(self.palm_normals[side], dtype=numpy.float64)
        palm = normalized(palm - direction * (palm @ direction))
        across = numpy.cross(direction, palm)
        curl = math.radians(self.finger_curls[side])
        spread = self.finger_spreads[side]
        palm_center = wrist + direction * 0.04 * size
        sculptor.ellipsoid(palm_center, direction, 0.045 * size, 0.042 * size, 0.02 * size, self.fur_mid,
                           up_hint=tuple(palm), mottle=0.08)
        for offset, scale in zip((-0.027, -0.009, 0.009, 0.027), (0.85, 1.0, 0.95, 0.8)):
            heading = normalized(direction + across * offset * spread * 10.0)
            points = [palm_center + direction * 0.04 * size + across * offset * size]
            for length in (0.035, 0.028, 0.022):
                heading = normalized(heading * math.cos(curl) + palm * math.sin(curl))
                points.append(points[-1] + heading * length * scale * size)
            sculptor.tube(points, ((0.0, 0.012 * size, 0.011 * size), (1.0, 0.008 * size, 0.0075 * size)),
                          self.fur_mid, rings=12, segments=10, mottle=0.08)
            claw_heading = normalized(heading * math.cos(curl) + palm * math.sin(curl))
            sculptor.spike(points[-1], claw_heading, 0.05 * scale, 0.009, self.claw,
                           curl=tuple(palm * 0.25))
        thumb_side = self.thumb_sides[side]
        heading = normalized(direction * 0.6 + across * thumb_side * 0.7 - palm * 0.2)
        points = [palm_center + across * thumb_side * 0.03 * size - direction * 0.01]
        for length in (0.03, 0.026):
            heading = normalized(heading * math.cos(curl * 0.6) + palm * math.sin(curl * 0.6))
            points.append(points[-1] + heading * length * size)
        sculptor.tube(points, ((0.0, 0.014 * size, 0.013 * size), (1.0, 0.009 * size, 0.0085 * size)), self.fur_mid,
                      rings=10, segments=10, mottle=0.08)
        sculptor.spike(points[-1], heading, 0.04, 0.009, self.claw, curl=tuple(palm * 0.25))

    def build_leg(self, side):
        sculptor = self.sculptor
        hip, knee, ankle, toe = (mirrored(point, side) for point in (self.hips, self.knees, self.ankles, self.toes))
        self.use_bones(side_name("thigh", side), side_name("shin", side))
        chunk = len(self.mesh.positions)
        sculptor.tube((hip, (hip + knee) / 2.0, knee), ((0.0, 0.095, 0.095), (0.5, 0.085, 0.09), (1.0, 0.062, 0.062)),
                      self.fur_mid, rings=14, segments=20, mottle=0.08)
        sculptor.ellipsoid(knee, (0.0, 1.0, 0.0), 0.058, 0.062, 0.062, self.fur_mid, mottle=0.08)
        self.grow_fur(chunk, self.thigh_fur, (0.0, -1.0, 0.0), (0.03, 0.06), (0.006, 0.01), 0.2,
                      lambda points, normals: points[:, 1] < 0.75)
        sculptor.tube((hip + (0.0, 0.02, 0.0), (hip + knee) / 2.0, knee + (0.0, -0.08, 0.0)),
                      ((0.0, 0.105, 0.105), (0.5, 0.098, 0.1), (1.0, 0.085, 0.085)), self.rags, rings=18,
                      segments=26, cap_start=False, cap_end=False, mottle=0.08, scales=self.trouser_folds)
        chunk = len(self.mesh.positions)
        sculptor.tube((knee, (knee + ankle) / 2.0 + (0.0, 0.0, -0.025), ankle),
                      ((0.0, 0.062, 0.062), (0.35, 0.06, 0.066), (1.0, 0.042, 0.042)), self.fur_mid, rings=16,
                      segments=20, mottle=0.08)
        self.grow_fur(chunk, self.shin_fur, (0.0, -1.0, -0.2), (0.035, 0.07), (0.007, 0.011), 0.25)
        self.use_bones(side_name("shin", side), side_name("foot", side))
        sculptor.ellipsoid(ankle + (0.0, -0.02, 0.02), (0.0, 0.0, 1.0), 0.07, 0.055, 0.055, self.fur_mid,
                           mottle=0.08)
        sculptor.ellipsoid((ankle + toe) / 2.0 + (0.0, -0.035, 0.0), toe - ankle, 0.15, 0.065, 0.032, self.fur_mid,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.08)
        for offset, length in zip((-0.045, -0.015, 0.015, 0.045), (0.8, 1.0, 1.0, 0.85)):
            root = toe + (offset * side, 0.0, -0.03)
            joint = root + (offset * side * 0.3, -0.005, 0.045 * length)
            tip = root + (offset * side * 0.5, -0.02, 0.075 * length)
            sculptor.tube((root, joint, tip), ((0.0, 0.017, 0.015), (1.0, 0.012, 0.01)), self.fur_mid, rings=10,
                          segments=10, mottle=0.08)
            sculptor.spike(tip, (offset * side * 0.4, -0.6, 1.0), 0.045 * length, 0.009, self.claw,
                           curl=(0.0, -0.25, 0.0))


class Werewolf(Vampire):

    def __init__(self, height, model=None):
        super().__init__(height, model)
        self.speech = Speech(seed=17)
        self.resting_gape = 0.45
        self.bite_degrees = 30.0
        self.cloth_flutter = 0.025
        self.eye_glow = 0.9
        self.skin_specular = (0.10, 0.11, 0.12, 1.0)
        self.skin_shininess = 10.0
        self.seated_thigh_pitch = -96.0
        self.seated_knee_spread = 12.0
        self.seated_chest = (8.0, 0.0, 0.0)
        self.seated_head = (-4.0, 0.0, 0.0)
        self.seated_upper_arm = (-22.0, 0.0, 12.0)
        self.seated_forearm = -55.0
        self.seated_hand = 10.0
        self.pose()

    def default_model(self):
        return WerewolfModel()

    def make_choreography(self):
        model = self.model
        return ClawLunge(model.standing_pose, model.stride, model.punching_side)

    def render(self):
        self.begin()
        self.draw(*self.cloth_skin.arrays())
        self.draw(*self.body_skin.arrays())
        self.draw_glowing(self.eye_skin, self.model.eye_color, self.eye_glow)
        self.end()
