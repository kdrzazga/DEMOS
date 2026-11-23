import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, catmull_rom, normalized
from lib.fantasy.anatomy import HairGrower, Jaw, MuscleRelief, Speech, smoothstep
from lib.fantasy.rig import Choreography, LabeledMesh, Skin, biped_skeleton, jaw_bone, mirrored, mirrored_all, \
    side_name
from lib.fantasy.sorcerer import RobeFolds


class PazureModel:

    def __init__(self, seed=13):
        self.generator = numpy.random.default_rng(seed)
        self.skin = (0.60, 0.41, 0.30)
        self.vein = (0.50, 0.33, 0.25)
        self.lip = (0.48, 0.30, 0.25)
        self.dark_crease = (0.12, 0.07, 0.06)
        self.eye_white = (0.82, 0.78, 0.72)
        self.iris = (0.16, 0.10, 0.06)
        self.nail = (0.66, 0.50, 0.42)
        self.hair_colors = ((0.17, 0.11, 0.07), (0.12, 0.08, 0.05), (0.22, 0.15, 0.10), (0.09, 0.06, 0.05))
        self.trousers = (0.20, 0.17, 0.13)
        self.belt = (0.12, 0.08, 0.06)
        self.buckle = (0.55, 0.52, 0.48)
        self.boot = (0.08, 0.065, 0.06)
        self.torso_points = ((0.0, 0.90, 0.0), (0.0, 1.12, 0.01), (0.0, 1.32, 0.01), (0.0, 1.47, -0.01),
                             (0.0, 1.53, -0.02))
        self.torso_profile = ((0.0, 0.15, 0.11), (0.25, 0.14, 0.105), (0.55, 0.18, 0.12), (0.8, 0.21, 0.125),
                              (0.93, 0.20, 0.11), (1.0, 0.10, 0.08))
        self.torso_relief = MuscleRelief(anchor=(0.0, 0.90, 0.0), axis=(0.0, 1.0, 0.0), anchor_height=0.90,
                                         lateral_scale=0.84, vertical_scale=0.85)
        self.torso_relief.ab_thickness = 0.004
        self.torso_relief.pec_thickness = 0.028
        self.torso_relief.pec_shelf = 0.4
        self.torso_relief.oblique_thickness = 0.006
        self.torso_relief.serratus_thickness = 0.003
        self.torso_relief.navel_depth = 0.005
        self.torso_relief.groin_depth = 0.004
        self.torso_relief.crease_darkening = 0.12
        self.torso_relief.groove_darkening = 0.04
        self.muscle_softness = 0.7
        self.vein_radius = 0.002
        self.pants_leg_offset = (0.0, 0.025)
        self.chest_hair_shade = 0.55
        self.shoulder = (0.22, 1.44, -0.01)
        self.elbow = (0.29, 1.15, -0.03)
        self.wrist = (0.32, 0.90, 0.04)
        self.hand_direction = (0.0, -1.0, 0.1)
        self.palm_normal = (-1.0, 0.0, 0.0)
        self.finger_curl = 25.0
        self.hip = (0.10, 0.93, 0.0)
        self.knee = (0.105, 0.50, 0.02)
        self.ankle = (0.10, 0.11, 0.0)
        self.toe = (0.10, 0.03, 0.18)
        self.waist_height = 1.02
        self.head_center = (0.0, 1.70, 0.01)
        self.jaw = Jaw(hinge=(0.0, 1.68, 0.02), lip_front=(0.0, 1.645, 0.11), half_width=0.075,
                       chin=(0.0, 1.605, 0.09), max_degrees=14.0)
        self.beard_count = 260
        self.mustache_count = 40
        self.sideburn_count = 40
        self.scalp_hair_count = 380
        self.hair_segments = 5
        self.colliders = [((0.0, 1.70, 0.01), 0.095), ((0.0, 1.635, 0.04), 0.068), ((0.0, 1.56, -0.01), 0.07)]
        self.beard_grower = HairGrower(self.generator, self.colliders, 0.018, 0.25, (0.0, -1.0, 0.1))
        self.scalp_grower = HairGrower(self.generator, self.colliders, 0.025, 0.35, (0.0, -1.0, -0.2))
        self.stride = 0.5
        self.standing_pose = {}
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.body, self.body_bones = self.built(self.build_body)
        self.shade_chest_hair(self.body)
        self.clothes, self.clothes_bones = self.built(self.build_clothes)
        self.hair_along = []
        self.hair_phases = []
        self.hair, self.hair_bones = self.built(self.build_hair)
        self.hair_along = numpy.concatenate(self.hair_along).astype(numpy.float32)
        self.hair_phases = numpy.concatenate(self.hair_phases).astype(numpy.float32)
        heights = numpy.concatenate([part[0][:, 1] for part in (self.body, self.clothes, self.hair)])
        self.bottom = float(heights.min())
        self.total_height = float(heights.max()) - self.bottom

    def build_skeleton(self):
        radii = {"pelvis": 0.17, "chest": 0.2, "head": 0.09, "upper_arm": 0.06, "forearm": 0.05, "hand": 0.04,
                 "thigh": 0.085, "shin": 0.06, "foot": 0.05, "waist_blend": 0.08, "neck_blend": 0.05,
                 "shoulder_blend": 0.06, "elbow_blend": 0.04, "wrist_blend": 0.025, "hip_blend": 0.06,
                 "knee_blend": 0.04, "ankle_blend": 0.03}
        wrist = numpy.asarray(self.wrist)
        return biped_skeleton(((0.0, 1.10, 0.0), (0.0, 0.85, 0.0)),
                              ((0.0, 1.10, 0.0), (0.0, 1.30, 0.0), (0.0, 1.50, -0.02)),
                              ((0.0, 1.52, -0.02), (0.0, 1.62, 0.0), (0.0, 1.72, 0.02)),
                              (self.shoulder, self.elbow), (self.elbow, self.wrist),
                              (self.wrist, tuple(wrist + normalized(self.hand_direction) * 0.17)),
                              (self.hip, self.knee), (self.knee, self.ankle), (self.ankle, self.toe),
                              radii, (jaw_bone(self.jaw, 0.03),))

    def use_bones(self, *names):
        self.mesh.bone_group = names

    def built(self, builder, group=("pelvis",)):
        self.mesh = LabeledMesh()
        self.mesh.bone_group = group
        self.sculptor.mesh = self.mesh
        builder()
        arrays = self.mesh.arrays()
        return arrays, self.mesh.bone_labels(self.skeleton, arrays[0])

    def shade_chest_hair(self, part):
        positions, _, colors, _ = part
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
        chest = ((1.0 - smoothstep((numpy.abs(x) - 0.06) / 0.08)) * smoothstep((y - 1.2) / 0.06)
                 * (1.0 - smoothstep((y - 1.43) / 0.04)) * (z > 0.06))
        trail = (1.0 - smoothstep(numpy.abs(x) / 0.025)) * smoothstep((y - 0.98) / 0.05) * (y < 1.25) * (z > 0.06)
        fuzz = 0.6 + 0.4 * numpy.abs(numpy.sin(x * 211.0 + y * 97.0) * numpy.sin(y * 173.0 - x * 61.0))
        darkening = numpy.clip(numpy.maximum(chest, 0.7 * trail) * fuzz, 0.0, 1.0) * self.chest_hair_shade
        colors *= (1.0 - darkening)[:, None].astype(numpy.float32)

    def build_body(self):
        self.use_bones("pelvis", "chest")
        self.sculptor.tube(self.torso_points, self.torso_profile, self.skin, up_hint=(0.0, 0.0, 1.0), mottle=0.05,
                           scales=self.torso_relief)
        self.use_bones("pelvis", "chest", "upper_arm_r", "upper_arm_l")
        self.build_shoulders()
        self.use_bones("chest", "head")
        self.build_neck()
        self.use_bones("head", "jaw")
        self.build_head()
        for side in (1.0, -1.0):
            self.use_bones(side_name("upper_arm", side), side_name("forearm", side))
            self.build_arm(side)
            self.use_bones(side_name("hand", side))
            self.build_hand(side)

    def build_shoulders(self):
        sculptor = self.sculptor
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.22, 1.43, -0.01), side), (side * 0.45, -1.0, 0.05), 0.09, 0.068, 0.062,
                               self.skin, up_hint=(0.0, 0.0, 1.0), rings=20, segments=24)
            sculptor.ellipsoid(mirrored((0.09, 1.495, -0.03), side), (side, -0.4, 0.0), 0.10, 0.038, 0.036, self.skin)

    def build_neck(self):
        sculptor = self.sculptor
        sculptor.tube(((0.0, 1.47, -0.02), (0.0, 1.55, -0.01), (0.0, 1.63, 0.0)),
                      ((0.0, 0.07, 0.065), (1.0, 0.058, 0.058)), self.skin, rings=14, segments=24,
                      up_hint=(0.0, 0.0, 1.0), cap_start=False, cap_end=False)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.04, 1.555, 0.03), side), (side * 0.4, -1.0, 0.6), 0.07, 0.022, 0.022,
                               self.skin)

    def build_head(self):
        sculptor = self.sculptor
        sculptor.ellipsoid(self.head_center, (0.0, 0.2, 1.0), 0.10, 0.078, 0.105, self.skin, up_hint=(0.0, 1.0, 0.0),
                           rings=22, segments=26)
        sculptor.ellipsoid((0.0, 1.635, 0.04), (0.0, -0.3, 1.0), 0.07, 0.068, 0.045, self.skin,
                           up_hint=(0.0, 1.0, 0.0))
        sculptor.ellipsoid((0.0, 1.612, 0.085), (0.0, -0.4, 1.0), 0.03, 0.03, 0.025, self.skin,
                           up_hint=(0.0, 1.0, 0.0))
        sculptor.ellipsoid((0.0, 1.735, 0.093), (1.0, 0.0, 0.0), 0.055, 0.018, 0.016, self.skin)
        sculptor.tube(((0.0, 1.725, 0.103), (0.0, 1.69, 0.118), (0.0, 1.672, 0.115)),
                      ((0.0, 0.012, 0.010), (0.7, 0.016, 0.014), (1.0, 0.011, 0.009)), self.skin, rings=12,
                      segments=12, up_hint=(0.0, 1.0, 0.0), cap_start=False)
        self.use_bones("head")
        sculptor.ellipsoid((0.0, 1.648, 0.104), (1.0, 0.0, 0.0), 0.026, 0.012, 0.006, self.dark_crease, mottle=0.0)
        sculptor.ellipsoid((0.0, 1.655, 0.108), (1.0, 0.0, 0.0), 0.024, 0.008, 0.006, self.lip, mottle=0.0)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.05, 1.69, 0.075), side), (side * 0.35, -0.2, 1.0), 0.035, 0.018, 0.016,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.033, 1.708, 0.086), side), (side, 0.0, 0.0), 0.014, 0.009, 0.008,
                               self.eye_white, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.033, 1.708, 0.094), side), (0.0, 0.0, 1.0), 0.003, 0.006, 0.006,
                               self.iris, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.033, 1.716, 0.092), side), (side, 0.1, 0.0), 0.016, 0.006, 0.005,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.035, 1.738, 0.094), side), (side, 0.25, -0.15), 0.026, 0.008, 0.006,
                               self.hair_colors[0], mottle=0.1)
            sculptor.ellipsoid(mirrored((0.012, 1.676, 0.112), side), (0.0, 0.0, 1.0), 0.01, 0.008, 0.007,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.079, 1.69, 0.0), side), (0.0, 1.0, 0.2), 0.03, 0.012, 0.02, self.skin)
        self.use_bones("jaw")
        sculptor.ellipsoid((0.0, 1.640, 0.105), (1.0, 0.0, 0.0), 0.023, 0.009, 0.007, self.lip, mottle=0.0)
        self.use_bones("head", "jaw")

    def build_arm(self, side):
        sculptor = self.sculptor
        shoulder, elbow, wrist = (mirrored(point, side) for point in (self.shoulder, self.elbow, self.wrist))
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0, elbow), ((0.0, 0.058, 0.058), (1.0, 0.045, 0.045)),
                      self.skin, rings=16, segments=22)
        along = elbow - shoulder
        softness = self.muscle_softness
        sculptor.ellipsoid((shoulder + elbow) / 2.0 + (0.0, -0.01, 0.035 * softness), along, 0.09,
                           0.045 * softness + 0.012, 0.04 * softness + 0.01, self.skin)
        sculptor.ellipsoid((shoulder + elbow) / 2.0 + (side * 0.01, 0.01, -0.035 * softness), along, 0.095,
                           0.045 * softness + 0.012, 0.04 * softness + 0.01, self.skin)
        sculptor.ellipsoid(elbow, along, 0.04, 0.045, 0.045, self.skin)
        sculptor.tube((elbow, (elbow + wrist) / 2.0, wrist), ((0.0, 0.05, 0.048), (0.35, 0.052, 0.048),
                                                              (1.0, 0.032, 0.026)), self.skin, rings=18, segments=22)
        forearm = wrist - elbow
        sculptor.ellipsoid(elbow + forearm * 0.3 + mirrored((0.014, 0.0, 0.01), side), forearm, 0.085, 0.03, 0.026,
                           self.skin)
        self.add_veins(side, shoulder, elbow, wrist)

    def add_veins(self, side, shoulder, elbow, wrist):
        generator = self.generator
        forearm = normalized(wrist - elbow)
        upper = normalized(elbow - shoulder)
        for start, end, axis, radius, offset_angle in ((elbow, wrist, forearm, 0.048, 0.3),
                                                       (elbow, wrist, forearm, 0.046, 1.1),
                                                       (shoulder + (elbow - shoulder) * 0.3, elbow, upper, 0.08, 0.1)):
            outward_start = normalized(numpy.cross(axis, (side, 0.0, 0.0)) if abs(axis[0]) < 0.9 else (0.0, 0.0, 1.0))
            sideways = numpy.cross(axis, outward_start)
            points = []
            for step in numpy.linspace(0.1, 0.9, 7):
                angle = offset_angle + 0.35 * math.sin(step * 9.0 + generator.uniform(0.0, 6.0))
                taper = 1.0 - 0.35 * step if radius < 0.06 else 1.0
                direction = outward_start * math.cos(angle) + sideways * math.sin(angle) * side
                points.append(start + (end - start) * step + direction * (radius * taper - self.vein_radius))
            centers = catmull_rom(points, 40)
            radii = numpy.full(len(centers), self.vein_radius)
            self.sculptor.sweep(centers, radii, radii, self.vein, segments=6, cap_start=True, cap_end=True, mottle=0.0)

    def build_hand(self, side):
        sculptor = self.sculptor
        wrist = mirrored(self.wrist, side)
        direction = normalized(self.hand_direction)
        palm = numpy.asarray(mirrored(self.palm_normal, side), dtype=numpy.float64)
        palm = normalized(palm - direction * (palm @ direction))
        across = numpy.cross(direction, palm)
        curl = math.radians(self.finger_curl)
        palm_center = wrist + direction * 0.045
        sculptor.ellipsoid(palm_center, direction, 0.05, 0.045, 0.018, self.skin, up_hint=tuple(palm))
        for offset, scale in zip((-0.03, -0.01, 0.01, 0.03), (0.85, 1.0, 0.95, 0.8)):
            heading = direction
            points = [palm_center + direction * 0.045 + across * offset]
            for length in (0.04, 0.028, 0.022):
                heading = normalized(heading * math.cos(curl) + palm * math.sin(curl))
                points.append(points[-1] + heading * length * scale)
            sculptor.tube(points, ((0.0, 0.012, 0.011), (1.0, 0.009, 0.008)), self.skin, rings=12, segments=10)
            sculptor.spike(points[-1], heading, 0.008, 0.007, self.nail)
        thumb_side = -side
        heading = normalized(direction * 0.6 + across * thumb_side * 0.6 + palm * 0.3)
        points = [palm_center + across * thumb_side * 0.035 - direction * 0.01]
        for length in (0.035, 0.028):
            heading = normalized(heading * math.cos(curl * 0.7) + palm * math.sin(curl * 0.7))
            points.append(points[-1] + heading * length)
        sculptor.tube(points, ((0.0, 0.015, 0.014), (1.0, 0.01, 0.009)), self.skin, rings=10, segments=10)

    def build_clothes(self):
        sculptor = self.sculptor
        self.use_bones("pelvis", "thigh_r", "thigh_l")
        sculptor.tube(((0.0, 1.04, 0.0), (0.0, 0.92, -0.005), (0.0, 0.78, 0.0)),
                      ((0.0, 0.165, 0.124), (0.5, 0.178, 0.132), (1.0, 0.176, 0.128)), self.trousers,
                      up_hint=(0.0, 0.0, 1.0), cap_start=False, mottle=0.06, scales=RobeFolds(9, 0.004, 0.01, 0.0,
                                                                                              1.0, 1, 30, 48))
        belt = [(0.163 * math.sin(angle), self.waist_height, 0.123 * math.cos(angle))
                for angle in numpy.linspace(0.0, 2.0 * math.pi, 33)]
        sculptor.tube(belt, ((0.0, 0.009, 0.02), (1.0, 0.009, 0.02)), self.belt, rings=96, segments=8,
                      up_hint=(0.0, 1.0, 0.0), cap_start=False, cap_end=False, mottle=0.05)
        sculptor.ellipsoid((0.0, self.waist_height, 0.133), (1.0, 0.0, 0.0), 0.03, 0.008, 0.024, self.buckle,
                           mottle=0.03)
        for side in (1.0, -1.0):
            hip, knee, ankle, toe = (mirrored(point, side) for point in (self.hip, self.knee, self.ankle, self.toe))
            hip_offset, knee_offset = (numpy.array((side * offset, 0.0, 0.0)) for offset in self.pants_leg_offset)
            self.use_bones(side_name("thigh", side))
            sculptor.tube((hip + hip_offset + (0.0, 0.03, 0.0), (hip + knee) / 2.0 + hip_offset, knee + knee_offset),
                          ((0.0, 0.09, 0.09), (0.45, 0.1, 0.098), (1.0, 0.105, 0.102)), self.trousers,
                          cap_start=False, cap_end=False, mottle=0.06,
                          scales=RobeFolds(7, 0.006, 0.012, 0.0, 1.0, 1, 30, 48))
            self.use_bones(side_name("thigh", side), side_name("shin", side))
            sculptor.ellipsoid(knee + knee_offset, (0.0, 1.0, 0.0), 0.06, 0.106, 0.104, self.trousers, mottle=0.06)
            self.use_bones(side_name("shin", side))
            sculptor.tube((knee + knee_offset, (knee + ankle) / 2.0 + knee_offset * 0.75,
                           ankle + knee_offset * 0.6 + (0.0, 0.03, 0.0)),
                          ((0.0, 0.105, 0.102), (0.5, 0.102, 0.1), (0.85, 0.098, 0.096), (1.0, 0.086, 0.084)),
                          self.trousers, cap_start=False, cap_end=False, mottle=0.06,
                          scales=RobeFolds(7, 0.008, 0.018, 0.0, 1.0, 1, 34, 48))
            self.use_bones(side_name("shin", side), side_name("foot", side))
            sculptor.ellipsoid(ankle + (0.0, -0.02, -0.01), (0.0, 1.0, 0.0), 0.06, 0.05, 0.055, self.boot,
                               mottle=0.04)
            sculptor.ellipsoid((ankle + toe) / 2.0 + (0.0, -0.025, 0.0), toe - ankle, 0.14, 0.05, 0.038, self.boot,
                               up_hint=(0.0, 1.0, 0.0), mottle=0.04)

    def add_strand(self, points, root_radius, root_weight_drop, tip_follows=None):
        generator = self.generator
        centers = catmull_rom(points, len(points) * 2)
        radii = numpy.linspace(root_radius, root_radius * 0.35, len(centers))
        color = numpy.asarray(self.hair_colors[generator.integers(len(self.hair_colors))]) * generator.uniform(0.85,
                                                                                                             1.15)
        along = numpy.repeat(numpy.linspace(0.0, 1.0, len(centers)), self.hair_segments + 1)
        self.mesh.next_weights = 1.0 - root_weight_drop * along
        self.mesh.next_blend_target = tip_follows
        self.sculptor.sweep(centers, radii, radii, color, segments=self.hair_segments, mottle=0.0)
        self.hair_along.append(along)
        self.hair_phases.append(numpy.full(len(along), generator.uniform(0.0, 2.0 * math.pi)))

    def scalp_direction(self):
        generator = self.generator
        while True:
            direction = generator.normal(0.0, 1.0, 3)
            direction /= numpy.linalg.norm(direction)
            if direction[1] > -0.05 and direction[2] < 0.55 - 0.5 * max(direction[1], 0.0) ** 2:
                return direction

    def build_hair(self):
        generator = self.generator
        self.use_bones("jaw")
        for _ in range(self.beard_count):
            angle = generator.uniform(-1.7, 1.7)
            height = generator.uniform(1.59, 1.665 + 0.02 * abs(angle))
            root = (math.sin(angle) * 0.07, height, 0.02 + math.cos(angle) * 0.075)
            heading = (math.sin(angle) * 0.6, -0.6, math.cos(angle) * 0.5)
            self.add_strand(self.beard_grower.grown(root, heading, int(generator.integers(2, 5)), 0.2), 0.004, 0.0)
        self.use_bones("head")
        for _ in range(self.mustache_count):
            side = generator.choice((-1.0, 1.0))
            root = (side * generator.uniform(0.004, 0.04), 1.659, 0.111)
            self.add_strand(self.beard_grower.grown(root, (side * 0.6, -1.0, 0.3), int(generator.integers(2, 4)), 0.3),
                            0.0035, 0.0)
        for _ in range(self.sideburn_count):
            side = generator.choice((-1.0, 1.0))
            root = (side * 0.077, generator.uniform(1.66, 1.73), generator.uniform(0.0, 0.035))
            self.add_strand(self.beard_grower.grown(root, (side * 0.5, -1.0, 0.1), int(generator.integers(2, 4)), 0.2),
                            0.004, 0.0)
        for _ in range(self.scalp_hair_count):
            direction = self.scalp_direction()
            root = numpy.asarray(self.head_center) + direction * (0.083, 0.103, 0.098)
            heading = direction + (0.0, 0.45, 0.0) + generator.normal(0.0, 0.3, 3)
            self.add_strand(self.scalp_grower.grown(root, heading, int(generator.integers(3, 7)), 0.08), 0.005, 0.0)


class Pazure:

    def __init__(self, height, model=None):
        self.model = model or PazureModel()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.acting = True
        self.talking = False
        self.speech = Speech(seed=12)
        self.hair_sway = 0.006
        self.hair_waves_along = 0.6
        self.breeze_per_second = 0.4
        self.skin_specular = (0.22, 0.18, 0.15, 1.0)
        self.skin_shininess = 24.0
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.advance = 0.0
        model = self.model
        self.ground = model.bottom
        self.choreography = Choreography(model.standing_pose, model.stride)
        self.body_skin = Skin(model.body, *model.body_bones, model.skeleton)
        self.clothes_skin = Skin(model.clothes, *model.clothes_bones, model.skeleton)
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
        self.clothes_skin.deform(matrices)
        self.hair_skin.deform(matrices, self.hair_positions)
        self.ground = self.clothes_skin.lowest() if self.acting else self.model.bottom

    def pose_hair(self):
        model = self.model
        along = model.hair_along
        wave = (self.seconds * self.breeze_per_second * 2.0 * math.pi + model.hair_phases
                - 2.0 * math.pi * self.hair_waves_along * along)
        amount = self.hair_sway * along ** 1.5
        rest = model.hair[0]
        self.hair_positions[:, 0] = rest[:, 0] + amount * numpy.sin(wave)
        self.hair_positions[:, 2] = rest[:, 2] + 0.6 * amount * numpy.cos(wave)

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

    def render(self):
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
        self.draw(*self.body_skin.arrays())
        self.draw(*self.clothes_skin.arrays())
        self.draw(*self.hair_skin.arrays())
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()
