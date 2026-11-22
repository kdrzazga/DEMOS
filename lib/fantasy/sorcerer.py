import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, catmull_rom, normalized, surface_normals, unit_or_fallback
from lib.animals.shark import hermite_profile
from lib.fantasy.anatomy import HairGrower, Jaw, Speech, smoothstep
from lib.fantasy.rig import Bone, Choreography, LabeledMesh, Skeleton, Skin, jaw_bone, mirrored, sided, translation, \
    mirrored_all, side_name


class RobeFolds:

    def __init__(self, fold_count, top_depth, bottom_depth, tatter_height, tatter_start, tatter_teeth, ring_count,
                 segment_count):
        self.fold_count = fold_count
        self.top_depth = top_depth
        self.bottom_depth = bottom_depth
        self.tatter_height = tatter_height
        self.tatter_start = tatter_start
        self.tatter_teeth = tatter_teeth
        self.ring_count = ring_count
        self.segment_count = segment_count
        self.fold_darkening = 0.3

    def rings(self, length):
        return self.ring_count

    def segments(self, widths, heights):
        return self.segment_count

    def displace(self, grid, centers, widths, heights, around):
        along = numpy.linspace(0.0, 1.0, grid.shape[0])[:, None]
        depth = self.top_depth + (self.bottom_depth - self.top_depth) * along ** 1.3
        wave = numpy.sin(around * self.fold_count + 0.7 * numpy.sin(around * 3.0 + 1.0))[None, :]
        outward = unit_or_fallback(grid - centers[:, None, :], numpy.zeros(3))
        grid = grid + outward * (depth * wave)[..., None]
        fraying = numpy.clip((along - self.tatter_start) / max(1.0 - self.tatter_start, 1e-6), 0.0, 1.0)
        teeth = numpy.abs(numpy.sin(around * self.tatter_teeth * 0.5 + 0.4 * numpy.sin(around * 11.0)))[None, :]
        grid[..., 1] += self.tatter_height * fraying * (1.0 - teeth ** 0.35)
        shade = 1.0 - self.fold_darkening * (0.5 - 0.5 * wave) * numpy.ones_like(along)
        return grid, shade


class StaffAttack(Choreography):

    def strike_hold_seconds(self):
        return 1.1

    def guard(self):
        pose = {"chest": (5.0, 15.0, 0.0), "head": (0.0, -15.0, 0.0), "staff_aim": (-20.0, 0.0, 0.0),
                "staff_slide": (0.3, 0.0, 0.0)}
        sided(pose, "upper_arm", 1.0, -60.0)
        sided(pose, "forearm", 1.0, -40.0)
        sided(pose, "upper_arm", -1.0, -40.0)
        sided(pose, "forearm", -1.0, -60.0)
        sided(pose, "thigh", -1.0, -22.0)
        sided(pose, "shin", -1.0, 25.0)
        sided(pose, "foot", -1.0, -3.0)
        sided(pose, "thigh", 1.0, 12.0)
        sided(pose, "shin", 1.0, 15.0)
        sided(pose, "foot", 1.0, -8.0)
        return pose

    def punch(self):
        pose = {"chest": (10.0, -8.0, 0.0), "head": (-5.0, 8.0, 0.0), "staff_aim": (78.0, 0.0, 0.0),
                "staff_slide": (0.75, 0.0, 0.0), "lightning": (1.0, 0.0, 0.0)}
        sided(pose, "upper_arm", 1.0, -90.0, 10.0)
        sided(pose, "forearm", 1.0, 0.0)
        sided(pose, "upper_arm", -1.0, 20.0)
        sided(pose, "forearm", -1.0, -30.0)
        sided(pose, "thigh", -1.0, -32.0)
        sided(pose, "shin", -1.0, 38.0)
        sided(pose, "foot", -1.0, -6.0)
        sided(pose, "thigh", 1.0, 20.0)
        sided(pose, "shin", 1.0, 12.0)
        sided(pose, "foot", 1.0, -12.0)
        return pose


class LightningBolts:

    def __init__(self, seed=17):
        self.generator = numpy.random.default_rng(seed)
        self.core_color = (0.96, 0.88, 1.0)
        self.glow_color = (0.72, 0.30, 1.0)
        self.spawn_gap_seconds = (0.04, 0.13)
        self.life_seconds = (0.06, 0.14)
        self.length = (0.35, 0.85)
        self.segments = 10
        self.jaggedness = 0.09
        self.spread = 0.35
        self.branch_chance = 0.65
        self.trigger = 0.5
        self.glow_width = 7.0
        self.core_width = 2.0
        self.bolts = []
        self.until_next = 0.0

    def update(self, seconds, intensity, origin, direction):
        for bolt in self.bolts:
            bolt[0] += seconds
        self.bolts = [bolt for bolt in self.bolts if bolt[0] < bolt[1]]
        if intensity < self.trigger:
            self.until_next = 0.0
            return
        self.until_next -= seconds
        while self.until_next <= 0.0:
            self.spawn(numpy.asarray(origin), numpy.asarray(direction))
            self.until_next += self.generator.uniform(*self.spawn_gap_seconds)

    def clear(self):
        self.bolts = []
        self.until_next = 0.0

    def jagged_path(self, origin, direction, length):
        generator = self.generator
        direction = normalized(direction + generator.normal(0.0, self.spread, 3))
        helper = numpy.array((0.0, 1.0, 0.0)) if abs(direction[1]) < 0.9 else numpy.array((1.0, 0.0, 0.0))
        across = normalized(numpy.cross(direction, helper))
        upward = numpy.cross(across, direction)
        steps = numpy.linspace(0.0, 1.0, self.segments + 1)
        wander = generator.normal(0.0, self.jaggedness * length, (self.segments + 1, 2))
        wander[0] = 0.0
        return [origin + direction * length * step + across * offset[0] + upward * offset[1]
                for step, offset in zip(steps, wander)]

    def spawn(self, origin, direction):
        generator = self.generator
        length = generator.uniform(*self.length)
        paths = [self.jagged_path(origin, direction, length)]
        if generator.uniform() < self.branch_chance:
            fork = paths[0][int(generator.integers(2, self.segments - 2))]
            paths.append(self.jagged_path(fork, direction, length * generator.uniform(0.3, 0.55)))
        self.bolts.append([0.0, generator.uniform(*self.life_seconds), paths])

    def flash(self):
        return min(1.0, sum(1.0 - age / life for age, life, _ in self.bolts))

    def render(self):
        if not self.bolts:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_LINE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        for width, color, opacity in ((self.glow_width, self.glow_color, 0.35), (self.core_width, self.core_color, 1.0)):
            glLineWidth(width)
            for age, life, paths in self.bolts:
                glColor4f(*color, opacity * (1.0 - age / life))
                for path in paths:
                    glBegin(GL_LINE_STRIP)
                    for point in path:
                        glVertex3f(*point)
                    glEnd()
        glPopAttrib()


class SorcererModel:

    def __init__(self, seed=21):
        self.generator = numpy.random.default_rng(seed)
        self.skin = (0.74, 0.62, 0.62)
        self.lip = (0.52, 0.36, 0.40)
        self.dark_crease = (0.10, 0.06, 0.09)
        self.robe = (0.15, 0.13, 0.20)
        self.mantle = (0.12, 0.11, 0.16)
        self.hood = (0.13, 0.12, 0.18)
        self.hood_lining = (0.05, 0.04, 0.07)
        self.trim = (0.44, 0.30, 0.58)
        self.trim_stitch = (0.70, 0.55, 0.85)
        self.belt = (0.20, 0.14, 0.13)
        self.metal = (0.55, 0.50, 0.62)
        self.boot = (0.10, 0.08, 0.09)
        self.trousers = (0.09, 0.08, 0.11)
        self.wood = (0.30, 0.22, 0.20)
        self.claw = (0.16, 0.13, 0.16)
        self.nail = (0.62, 0.55, 0.52)
        self.eye_color = (1.0, 0.45, 1.0)
        self.crystal_color = (0.78, 0.50, 1.0)
        self.orb_color = (0.95, 0.40, 1.0)
        self.hair_colors = ((0.72, 0.68, 0.76), (0.60, 0.56, 0.66), (0.84, 0.80, 0.88), (0.50, 0.46, 0.56))
        self.robe_points = ((0.0, 1.56, -0.01), (0.0, 1.10, 0.0), (0.0, 0.55, 0.0), (0.0, 0.02, 0.01))
        self.robe_profile = ((0.0, 0.17, 0.12), (0.10, 0.21, 0.14), (0.28, 0.17, 0.13), (0.45, 0.20, 0.16),
                             (0.75, 0.27, 0.22), (1.0, 0.36, 0.30))
        self.robe_folds = RobeFolds(16, 0.006, 0.03, 0.11, 0.92, 26, 90, 96)
        self.mantle_points = ((0.0, 1.64, -0.02), (0.0, 1.40, -0.03), (0.0, 1.18, -0.04))
        self.mantle_profile = ((0.0, 0.11, 0.10), (0.18, 0.27, 0.17), (0.5, 0.31, 0.21), (1.0, 0.34, 0.23))
        self.mantle_folds = RobeFolds(12, 0.008, 0.02, 0.09, 0.7, 18, 40, 80)
        self.sleeve_folds = RobeFolds(6, 0.004, 0.012, 0.05, 0.8, 10, 24, 48)
        self.waist_height = 1.13
        self.head_center = (0.0, 1.71, 0.02)
        self.hood_center = (0.0, 1.71, -0.01)
        self.hood_radii = (0.135, 0.16, 0.15)
        self.hood_opening = 0.75
        self.hood_bottom = 2.2
        self.hood_peak = (0.0, 0.55, -0.83)
        self.hood_peak_lift = 0.5
        self.hood_thickness = 0.006
        self.hood_neck_height = 1.60
        self.hood_neck_blend = 0.12
        self.shoulders = {1.0: (0.20, 1.50, -0.01), -1.0: (-0.20, 1.50, -0.01)}
        self.elbows = {1.0: (0.30, 1.24, 0.02), -1.0: (-0.30, 1.25, 0.08)}
        self.wrists = {1.0: (0.33, 1.06, 0.17), -1.0: (-0.29, 1.15, 0.32)}
        self.hand_directions = {1.0: (0.1, -0.05, 1.0), -1.0: (0.0, -0.2, 1.0)}
        self.palm_normals = {1.0: (-1.0, 0.0, 0.0), -1.0: (0.0, -1.0, 0.15)}
        self.finger_curls = {1.0: 62.0, -1.0: 18.0}
        self.finger_spreads = {1.0: 0.0, -1.0: 1.0}
        self.thumb_sides = {1.0: -1.0, -1.0: 1.0}
        self.staff_points = ((0.36, 0.01, 0.30), (0.335, 0.55, 0.27), (0.31, 1.056, 0.245), (0.30, 1.6, 0.225),
                             (0.29, 2.06, 0.21))
        self.staff_grip = (0.31, 1.056, 0.245)
        self.crystal_center = (0.29, 2.17, 0.21)
        self.staff_axis = normalized(numpy.asarray(self.staff_points[-1]) - numpy.asarray(self.staff_grip))
        self.crystal_tip = numpy.asarray(self.crystal_center) + self.staff_axis * 0.12
        self.jaw = Jaw(hinge=(0.0, 1.69, 0.04), lip_front=(0.0, 1.655, 0.13), half_width=0.07,
                       chin=(0.0, 1.615, 0.11), max_degrees=14.0)
        self.hips = (0.09, 0.98, 0.0)
        self.knees = (0.10, 0.52, 0.03)
        self.ankles = (0.09, 0.09, 0.02)
        self.toes = (0.09, 0.03, 0.31)
        self.robe_leg_start = 1.0
        self.robe_leg_fade = 0.35
        self.robe_leg_seam = 0.1
        self.robe_leg_share = 0.75
        self.stride = 0.5
        self.punching_side = 1.0
        self.standing_pose = {"forearm_r": (40.0, 0.0, 0.0), "forearm_l": (68.0, 0.0, 0.0)}
        self.beard_count = 70
        self.mustache_count = 16
        self.hair_count = 60
        self.hair_segments = 5
        self.beard_stiffness = 0.85
        self.hair_stiffness = 0.75
        self.colliders = [((0.0, 1.71, 0.02), 0.10), ((0.0, 1.52, -0.02), 0.21), ((0.0, 1.40, 0.0), 0.26),
                          ((0.0, 1.15, 0.0), 0.21), ((0.0, 0.95, 0.0), 0.22), ((0.2, 1.48, -0.01), 0.16),
                          ((-0.2, 1.48, -0.01), 0.16)]
        self.hair_grower = HairGrower(self.generator, self.colliders, 0.035, 0.08, (0.0, -1.0, 0.05))
        self.hair_along = []
        self.hair_phases = []
        self.skeleton = self.build_skeleton()
        self.mesh = LabeledMesh()
        self.sculptor = Sculptor(self.mesh)
        self.cloth, self.cloth_bones = self.built(self.build_cloth)
        self.attach_robe_to_legs()
        self.body, self.body_bones = self.built(self.build_body)
        self.staff, self.staff_bones = self.built(self.build_staff, ("staff",))
        self.eyes, self.eye_bones = self.built(self.build_eyes, ("head",))
        self.crystal, self.crystal_bones = self.built(self.build_crystal, ("staff",))
        self.orb, self.orb_bones = self.built(self.build_orb, ("hand_l",))
        self.hair, self.hair_bones = self.built(self.build_hair)
        self.hair_along = numpy.concatenate(self.hair_along).astype(numpy.float32)
        self.hair_phases = numpy.concatenate(self.hair_phases).astype(numpy.float32)
        self.cloth_looseness = self.looseness(self.cloth[0])
        heights = numpy.concatenate([part[0][:, 1] for part in (self.cloth, self.body, self.staff, self.crystal)])
        self.bottom = float(heights.min())
        self.total_height = float(heights.max()) - self.bottom

    def build_skeleton(self):
        bones = [Bone("pelvis", None, ((0.0, 1.10, 0.0), (0.0, 0.5, 0.0)), 0.25, 0.0),
                 Bone("chest", "pelvis", ((0.0, 1.12, 0.0), (0.0, 1.40, 0.0), (0.0, 1.58, -0.01)), 0.22, 0.10),
                 Bone("head", "chest", ((0.0, 1.58, -0.01), (0.0, 1.70, 0.03), (0.0, 1.80, 0.05)), 0.12, 0.05),
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
        bones.append(Bone("staff", "hand_r", (self.staff_grip, self.staff_points[-1]), 0.05, 0.0))
        return Skeleton(bones)

    def use_bones(self, *names):
        self.mesh.bone_group = names

    def built(self, builder, group=("pelvis",)):
        self.mesh = LabeledMesh()
        self.mesh.bone_group = group
        self.sculptor.mesh = self.mesh
        builder()
        arrays = self.mesh.arrays()
        return arrays, self.mesh.bone_labels(self.skeleton, arrays[0])

    @staticmethod
    def looseness(positions):
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
        hem = numpy.clip((0.95 - y) / 0.95, 0.0, 1.0) ** 1.5
        reach = numpy.hypot(x, z)
        hanging = numpy.clip((1.32 - y) / 0.14, 0.0, 1.0) * numpy.clip((reach - 0.2) / 0.1, 0.0, 1.0) * (y > 0.95)
        return numpy.maximum(hem, 0.6 * hanging).astype(numpy.float32)

    def robe_surface_depth(self, along, lateral):
        knots, widths, depths = (numpy.array(column) for column in zip(*self.robe_profile))
        width = float(hermite_profile(knots, widths, numpy.array([along]))[0])
        depth = float(hermite_profile(knots, depths, numpy.array([along]))[0])
        return depth * math.sqrt(max(1.0 - (lateral / width) ** 2, 0.0))

    def build_cloth(self):
        sculptor = self.sculptor
        self.use_bones("pelvis", "chest")
        sculptor.tube(self.robe_points, self.robe_profile, self.robe, up_hint=(0.0, 0.0, 1.0), cap_end=False,
                      mottle=0.04, scales=self.robe_folds)
        self.build_trim()
        self.leg_draped_count = self.mesh.vertex_count
        self.use_bones("pelvis", "chest")
        belt_ring = [(0.185 * math.sin(angle), self.waist_height, 0.145 * math.cos(angle))
                     for angle in numpy.linspace(0.0, 2.0 * math.pi, 33)]
        sculptor.tube(belt_ring, ((0.0, 0.014, 0.022), (1.0, 0.014, 0.022)), self.belt, rings=96, segments=8,
                      up_hint=(0.0, 1.0, 0.0), cap_start=False, cap_end=False, mottle=0.03)
        sculptor.ellipsoid((0.0, self.waist_height, 0.16), (1.0, 0.0, 0.0), 0.03, 0.012, 0.026, self.metal,
                           mottle=0.02)
        self.use_bones("chest")
        sculptor.ellipsoid((0.0, 1.43, 0.155), (0.0, 0.0, 1.0), 0.008, 0.035, 0.035, self.metal, mottle=0.02)
        self.use_bones("chest", "upper_arm_r", "upper_arm_l")
        sculptor.tube(self.mantle_points, self.mantle_profile, self.mantle, up_hint=(0.0, 0.0, 1.0),
                      cap_start=False, cap_end=False, mottle=0.04, scales=self.mantle_folds)
        for side in (1.0, -1.0):
            self.build_sleeve(side)
        self.use_bones("head")
        self.build_hood()

    def build_trim(self):
        self.use_bones("pelvis", "chest")
        samples = numpy.linspace(0.06, 0.97, 30)
        top, bottom = self.robe_points[0][1], self.robe_points[-1][1]
        stitches = (numpy.sin(numpy.linspace(0.0, 60.0, 30 * 4)) > 0.4)[:, None, None]
        colors = numpy.where(stitches, numpy.asarray(self.trim_stitch), numpy.asarray(self.trim))
        for lateral in (-0.045, 0.045):
            points = [(lateral, top + (bottom - top) * along, self.robe_surface_depth(along, lateral) + 0.012)
                      for along in samples]
            centers = catmull_rom(points, len(points) * 4)
            radii = numpy.full(len(centers), 0.009)
            self.sculptor.sweep(centers, radii * 1.4, radii * 0.6, colors, up_hint=(0.0, 0.0, 1.0), segments=8,
                                mottle=0.02)

    def build_sleeve(self, side):
        sculptor = self.sculptor
        shoulder, elbow, wrist = (numpy.asarray(point) for point in
                                  (self.shoulders[side], self.elbows[side], self.wrists[side]))
        self.use_bones(side_name("upper_arm", side))
        sculptor.tube((shoulder, (shoulder + elbow) / 2.0, elbow), ((0.0, 0.072, 0.072), (1.0, 0.078, 0.078)),
                      self.robe, rings=16, segments=24, mottle=0.04)
        sculptor.ellipsoid(elbow, elbow - shoulder, 0.07, 0.08, 0.08, self.robe, mottle=0.04)
        self.use_bones(side_name("forearm", side))
        cuff = wrist + normalized(wrist - elbow) * 0.015
        sculptor.tube((elbow, (elbow + cuff) / 2.0, cuff), ((0.0, 0.078, 0.078), (0.6, 0.09, 0.09), (1.0, 0.115, 0.11)),
                      self.robe, cap_start=False, cap_end=False, mottle=0.04, scales=self.sleeve_folds)

    def build_hood(self):
        polar = numpy.linspace(0.0, self.hood_bottom, 26)
        azimuth = numpy.linspace(self.hood_opening, 2.0 * math.pi - self.hood_opening, 44)
        polar, azimuth = numpy.meshgrid(polar, azimuth, indexing="ij")
        direction = numpy.stack((numpy.sin(polar) * numpy.sin(azimuth), numpy.cos(polar),
                                 numpy.sin(polar) * numpy.cos(azimuth)), axis=-1)
        peak = numpy.clip(direction @ normalized(self.hood_peak), 0.0, None) ** 3
        center = numpy.asarray(self.hood_center)
        grid = center + direction * numpy.asarray(self.hood_radii) * (1.0 + self.hood_peak_lift * peak)[..., None]
        normals = unit_or_fallback(surface_normals(grid, center, False), direction)
        edge = numpy.clip(1.0 - numpy.minimum(azimuth - self.hood_opening,
                                              2.0 * math.pi - self.hood_opening - azimuth) / 0.25, 0.0, 1.0)
        outer = numpy.asarray(self.hood) * (1.0 + 0.35 * edge)[..., None]
        inner = numpy.broadcast_to(numpy.asarray(self.hood_lining), grid.shape)
        head_following = smoothstep((grid[..., 1] - self.hood_neck_height) / self.hood_neck_blend)
        self.mesh.next_weights = head_following
        self.mesh.add_grid(grid + normals * self.hood_thickness, normals, outer)
        self.mesh.next_weights = head_following
        self.mesh.add_grid(grid - normals * self.hood_thickness, -normals, inner)

    def build_body(self):
        self.use_bones("head", "jaw")
        self.build_face()
        for side in (1.0, -1.0):
            self.use_bones(side_name("hand", side))
            self.build_hand(side)
        for side in (1.0, -1.0):
            self.build_leg(side)

    def attach_robe_to_legs(self):
        labels, overrides, _ = self.cloth_bones
        positions = self.cloth[0][:self.leg_draped_count].astype(numpy.float64)
        hanging = positions[:, 1] < self.robe_leg_start
        right, left = self.skeleton.index["thigh_r"], self.skeleton.index["thigh_l"]
        draped = numpy.nonzero(hanging)[0]
        lateral = positions[draped, 0]
        labels[draped] = numpy.where(lateral >= 0.0, right, left)
        overrides[draped] = (self.robe_leg_share * smoothstep(numpy.abs(lateral) / self.robe_leg_seam)
                             * smoothstep((self.robe_leg_start - positions[draped, 1]) / self.robe_leg_fade))

    def build_leg(self, side):
        sculptor = self.sculptor
        hip, knee, ankle, toe = (mirrored(point, side) for point in (self.hips, self.knees, self.ankles, self.toes))
        self.use_bones(side_name("thigh", side), side_name("shin", side))
        sculptor.tube((hip, (hip + knee) / 2.0, knee), ((0.0, 0.075, 0.075), (1.0, 0.055, 0.055)), self.trousers,
                      rings=14, segments=18, mottle=0.04)
        sculptor.ellipsoid(knee, (0.0, 1.0, 0.0), 0.05, 0.055, 0.055, self.trousers, mottle=0.04)
        sculptor.tube((knee, (knee + ankle) / 2.0, ankle), ((0.0, 0.055, 0.055), (1.0, 0.045, 0.045)), self.trousers,
                      rings=14, segments=18, mottle=0.04)
        self.use_bones(side_name("shin", side), side_name("foot", side))
        sculptor.ellipsoid(ankle + (0.0, -0.015, 0.0), (0.0, 0.0, 1.0), 0.06, 0.05, 0.055, self.boot, mottle=0.03)
        sculptor.ellipsoid((ankle + toe) / 2.0 + (0.0, -0.025, 0.0), toe - ankle, 0.165, 0.05, 0.035, self.boot,
                           up_hint=(0.0, 1.0, 0.0), mottle=0.03)

    def build_face(self):
        sculptor = self.sculptor
        sculptor.ellipsoid(self.head_center, (0.0, 0.15, 1.0), 0.105, 0.085, 0.11, self.skin, up_hint=(0.0, 1.0, 0.0),
                           rings=20, segments=24)
        sculptor.ellipsoid((0.0, 1.635, 0.085), (0.0, -0.4, 1.0), 0.055, 0.06, 0.04, self.skin,
                           up_hint=(0.0, 1.0, 0.0))
        sculptor.tube(((0.0, 1.745, 0.122), (0.0, 1.712, 0.152), (0.0, 1.688, 0.164)),
                      ((0.0, 0.014, 0.012), (0.6, 0.018, 0.016), (1.0, 0.012, 0.010)), self.skin, rings=14,
                      segments=14, up_hint=(0.0, 1.0, 0.0), cap_start=False)
        self.use_bones("jaw")
        sculptor.ellipsoid((0.0, 1.648, 0.121), (1.0, 0.0, 0.0), 0.026, 0.008, 0.006, self.lip, mottle=0.0)
        self.use_bones("head")
        sculptor.ellipsoid((0.0, 1.652, 0.105), (1.0, 0.0, 0.0), 0.03, 0.02, 0.012, self.dark_crease, mottle=0.0)
        sculptor.ellipsoid((0.0, 1.66, 0.124), (1.0, 0.0, 0.0), 0.028, 0.008, 0.006, self.lip, mottle=0.0)
        for side in (1.0, -1.0):
            sculptor.ellipsoid(mirrored((0.033, 1.722, 0.104), side), (0.0, 0.0, 1.0), 0.012, 0.022, 0.016,
                               self.dark_crease, mottle=0.0)
            sculptor.ellipsoid(mirrored((0.035, 1.742, 0.117), side), (side, 0.35, -0.2), 0.035, 0.014, 0.012,
                               self.hair_colors[2], mottle=0.08)
            sculptor.ellipsoid(mirrored((0.055, 1.705, 0.092), side), (side * 0.35, -0.2, 1.0), 0.04, 0.02, 0.016,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.014, 1.684, 0.152), side), (0.0, 0.0, 1.0), 0.012, 0.009, 0.008,
                               self.skin)
            sculptor.ellipsoid(mirrored((0.058, 1.672, 0.085), side), (side * 0.2, -0.5, 1.0), 0.03, 0.015, 0.012,
                               self.skin)
        self.use_bones("head", "jaw")

    def build_hand(self, side):
        sculptor = self.sculptor
        wrist = numpy.asarray(self.wrists[side], dtype=numpy.float64)
        direction = normalized(self.hand_directions[side])
        palm = numpy.asarray(self.palm_normals[side], dtype=numpy.float64)
        palm = normalized(palm - direction * (palm @ direction))
        across = numpy.cross(direction, palm)
        curl = math.radians(self.finger_curls[side])
        spread = self.finger_spreads[side]
        palm_center = wrist + direction * 0.04
        sculptor.ellipsoid(palm_center, direction, 0.045, 0.04, 0.016, self.skin, up_hint=tuple(palm))
        for offset, scale in zip((-0.027, -0.009, 0.009, 0.027), (0.85, 1.0, 0.95, 0.8)):
            heading = normalized(direction + across * offset * spread * 10.0)
            points = [palm_center + direction * 0.04 + across * offset]
            for length in (0.035, 0.026, 0.02):
                heading = normalized(heading * math.cos(curl) + palm * math.sin(curl))
                points.append(points[-1] + heading * length * scale)
            sculptor.tube(points, ((0.0, 0.011, 0.010), (1.0, 0.007, 0.0065)), self.skin, rings=12, segments=10)
            for joint in points[:-1]:
                sculptor.ellipsoid(joint, heading, 0.011, 0.011, 0.010, self.skin, rings=8, segments=10)
            sculptor.spike(points[-1], heading, 0.01, 0.006, self.nail)
        thumb_side = self.thumb_sides[side]
        heading = normalized(direction * 0.6 + across * thumb_side * 0.7 - palm * 0.2)
        points = [palm_center + across * thumb_side * 0.03 - direction * 0.01]
        for length in (0.03, 0.025):
            heading = normalized(heading * math.cos(curl * 0.6) + palm * math.sin(curl * 0.6))
            points.append(points[-1] + heading * length)
        sculptor.tube(points, ((0.0, 0.013, 0.012), (1.0, 0.008, 0.0075)), self.skin, rings=10, segments=10)

    def build_staff(self):
        sculptor = self.sculptor
        centers = catmull_rom(self.staff_points, 120)
        along = numpy.linspace(0.0, 1.0, len(centers))
        gnarl = 1.0 + 0.18 * numpy.sin(along * 47.0) * numpy.sin(along * 13.0 + 1.0)
        radii = (0.019 + 0.006 * along) * gnarl
        sculptor.sweep(centers, radii, radii * 0.9, self.wood, segments=12, cap_start=True, mottle=0.12)
        top = numpy.asarray(self.staff_points[-1])
        crystal = numpy.asarray(self.crystal_center)
        for prong in range(4):
            angle = prong * math.pi / 2.0 + math.pi / 4.0
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            path = (top - (0.0, 0.03, 0.0), top + outward * 0.05 + (0.0, 0.06, 0.0),
                    crystal + outward * 0.05 + (0.0, 0.02, 0.0), crystal + outward * 0.02 + (0.0, 0.10, 0.0))
            sculptor.tube(path, ((0.0, 0.012, 0.012), (0.7, 0.008, 0.008), (1.0, 0.0015, 0.0015)), self.claw,
                          rings=20, segments=8, cap_end=False, mottle=0.05)
        for knot in (0.35, 0.62, 0.8):
            index = int(knot * (len(centers) - 1))
            sculptor.ellipsoid(centers[index], (0.0, 1.0, 0.0), 0.03, radii[index] * 1.35, radii[index] * 1.3,
                               self.wood, mottle=0.12)

    def build_crystal(self):
        center = numpy.asarray(self.crystal_center)
        self.sculptor.tube((center - (0.0, 0.09, 0.0), center, center + (0.0, 0.11, 0.0)),
                           ((0.0, 0.0, 0.0), (0.35, 0.038, 0.038), (0.55, 0.042, 0.042), (1.0, 0.0, 0.0)),
                           self.crystal_color, rings=16, segments=6, cap_start=False, cap_end=False, mottle=0.0)

    def orb_center(self):
        side = -1.0
        wrist = numpy.asarray(self.wrists[side])
        direction = normalized(self.hand_directions[side])
        palm = normalized(self.palm_normals[side])
        return wrist + direction * 0.09 + palm * 0.05

    def build_orb(self):
        self.sculptor.ellipsoid(self.orb_center(), (0.0, 1.0, 0.0), 0.022, 0.022, 0.022, self.orb_color, mottle=0.0)

    def build_eyes(self):
        for side in (1.0, -1.0):
            self.sculptor.ellipsoid(mirrored((0.033, 1.722, 0.112), side), (side, 0.15, 0.0), 0.014, 0.006, 0.007,
                                    self.eye_color, mottle=0.0)

    def add_strand(self, points, root_radius, stiffness, tip_follows=None):
        generator = self.generator
        centers = catmull_rom(points, len(points) * 2)
        radii = numpy.linspace(root_radius, root_radius * 0.25, len(centers))
        color = numpy.asarray(self.hair_colors[generator.integers(len(self.hair_colors))]) * generator.uniform(0.85,
                                                                                                             1.1)
        along = numpy.repeat(numpy.linspace(0.0, 1.0, len(centers)), self.hair_segments + 1)
        self.mesh.next_weights = 1.0 - stiffness * along
        self.mesh.next_blend_target = tip_follows
        self.sculptor.sweep(centers, radii, radii, color, segments=self.hair_segments, mottle=0.0)
        self.hair_along.append(along)
        self.hair_phases.append(numpy.full(len(along), generator.uniform(0.0, 2.0 * math.pi)))

    def build_hair(self):
        generator = self.generator
        grower = self.hair_grower
        self.use_bones("jaw")
        for _ in range(self.beard_count):
            angle = generator.uniform(-1.6, 1.6)
            height = generator.uniform(1.60, 1.665)
            root = (math.sin(angle) * 0.07, height, 0.035 + math.cos(angle) * 0.075)
            heading = (math.sin(angle) * 0.25, -1.0, 0.55)
            self.add_strand(grower.grown(root, heading, int(generator.integers(9, 17)), 0.25), 0.007,
                            self.beard_stiffness, "chest")
        self.use_bones("head")
        for _ in range(self.mustache_count):
            side = generator.choice((-1.0, 1.0))
            root = (side * generator.uniform(0.005, 0.045), 1.668, 0.128)
            self.add_strand(grower.grown(root, (side, -0.5, 0.2), int(generator.integers(3, 6)), 0.35), 0.005,
                            0.0)
        for _ in range(self.hair_count):
            side = generator.choice((-1.0, 1.0))
            angle = side * generator.uniform(0.9, 1.7)
            root = (math.sin(angle) * 0.085, generator.uniform(1.70, 1.80), 0.02 + math.cos(angle) * 0.09)
            self.add_strand(grower.grown(root, (math.sin(angle) * 0.4, -1.0, 0.15), int(generator.integers(12, 21)),
                                         0.25), 0.007, self.hair_stiffness, "chest")


class Sorcerer:

    def __init__(self, height, model=None):
        self.model = model or SorcererModel()
        self.height = height
        self.position = (0.0, 0.0, 0.0)
        self.yaw = 0.0
        self.acting = True
        self.talking = False
        self.speech = Speech(seed=9)
        self.power = 0.3
        self.cloth_flutter = 0.035
        self.flutter_per_second = 0.45
        self.hair_sway = 0.012
        self.hair_waves_along = 0.7
        self.breeze_per_second = 0.3
        self.eye_glow = 1.1
        self.crystal_pulses_per_second = 0.8
        self.crystal_glow = 0.9
        self.orb_glow = 1.0
        self.crystal_light = (0.80, 0.32, 1.0)
        self.hand_light = (0.95, 0.35, 1.0)
        self.light_attenuation = (0.6, 0.0, 3.5)
        self.skin_specular = (0.18, 0.14, 0.22, 1.0)
        self.skin_shininess = 18.0
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.advance = 0.0
        model = self.model
        self.ground = model.bottom
        skeleton = model.skeleton
        self.staff_carriers = ("chest", "upper_arm_r", "forearm_r")
        self.choreography = StaffAttack(model.standing_pose, model.stride, model.punching_side)
        self.lightning = 0.0
        self.bolts = LightningBolts()
        self.cloth_skin = Skin(model.cloth, *model.cloth_bones, skeleton)
        self.body_skin = Skin(model.body, *model.body_bones, skeleton)
        self.staff_skin = Skin(model.staff, *model.staff_bones, skeleton)
        self.eye_skin = Skin(model.eyes, *model.eye_bones, skeleton)
        self.crystal_skin = Skin(model.crystal, *model.crystal_bones, skeleton)
        self.orb_skin = Skin(model.orb, *model.orb_bones, skeleton)
        self.hair_skin = Skin(model.hair, *model.hair_bones, skeleton)
        self.cloth_positions = model.cloth[0].copy()
        self.hair_positions = model.hair[0].copy()
        self.matrices = skeleton.matrices({}, (0.0, 0.0, 0.0))
        self.pose()

    def restart(self):
        self.seconds = 0.0
        self.act_seconds = 0.0
        self.bolts.clear()
        self.pose()

    def update(self, seconds):
        self.seconds += seconds
        if self.acting:
            self.act_seconds += seconds
        self.pose()
        origin = self.bone_point("staff", self.model.crystal_tip)
        direction = self.bone_direction("staff", self.model.staff_axis)
        self.bolts.update(seconds, self.lightning, origin, direction)

    def pose(self):
        self.pose_cloth()
        self.pose_hair()
        angles, self.advance = self.choreography.pose_at(self.act_seconds) if self.acting else ({}, 0.0)
        aim = self.cue(angles, "staff_aim")
        slide = self.cue(angles, "staff_slide")
        self.lightning = self.cue(angles, "lightning")
        self.aim_staff(angles, aim)
        if self.talking:
            angles["jaw"] = (self.model.jaw.max_degrees * self.speech.openness(self.seconds), 0.0, 0.0)
        self.matrices = self.model.skeleton.matrices(angles, (0.0, 0.0, self.advance))
        staff = self.model.skeleton.index["staff"]
        self.matrices[staff] = self.matrices[staff] @ translation(self.model.staff_axis * slide)
        self.cloth_skin.deform(self.matrices, self.cloth_positions)
        self.body_skin.deform(self.matrices)
        self.staff_skin.deform(self.matrices)
        self.eye_skin.deform(self.matrices)
        self.crystal_skin.deform(self.matrices)
        self.orb_skin.deform(self.matrices)
        self.hair_skin.deform(self.matrices, self.hair_positions)
        self.ground = self.body_skin.lowest() if self.acting else self.model.bottom

    @staticmethod
    def cue(angles, name):
        return angles.pop(name, (0.0, 0.0, 0.0))[0]

    def aim_staff(self, angles, aim):
        tilt = sum(angles.get(name, (0.0, 0.0, 0.0))[0] for name in self.staff_carriers)
        hand = angles.get("hand_r", (0.0, 0.0, 0.0))
        angles["hand_r"] = (aim - tilt, hand[1], hand[2])

    def pose_cloth(self):
        model = self.model
        rest = model.cloth[0]
        phase = self.seconds * self.flutter_per_second * 2.0 * math.pi
        amount = self.cloth_flutter * model.cloth_looseness
        self.cloth_positions[:, 0] = rest[:, 0] + amount * numpy.sin(phase + rest[:, 1] * 6.0 + rest[:, 0] * 4.0)
        self.cloth_positions[:, 2] = rest[:, 2] + 0.6 * amount * numpy.cos(1.3 * phase + rest[:, 1] * 5.0
                                                                          + rest[:, 2] * 3.0)

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

    def pulse(self):
        return 0.85 + 0.15 * math.sin(self.seconds * self.crystal_pulses_per_second * 2.0 * math.pi)

    def bone_direction(self, name, direction):
        return tuple(self.matrices[self.model.skeleton.index[name]][:3, :3] @ numpy.asarray(direction))

    def bone_point(self, name, point):
        matrix = self.matrices[self.model.skeleton.index[name]]
        return tuple(matrix[:3, :3] @ numpy.asarray(point) + matrix[:3, 3])

    def place_light(self, light, position, color, strength):
        constant, linear, quadratic = self.light_attenuation
        glEnable(light)
        glLightfv(light, GL_POSITION, (*position, 1.0))
        glLightfv(light, GL_DIFFUSE, (*(numpy.asarray(color) * strength), 1.0))
        glLightfv(light, GL_SPECULAR, (*(numpy.asarray(color) * strength * 0.6), 1.0))
        glLightfv(light, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(light, GL_CONSTANT_ATTENUATION, constant)
        glLightf(light, GL_LINEAR_ATTENUATION, linear)
        glLightf(light, GL_QUADRATIC_ATTENUATION, quadratic)

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
        strength = self.pulse() * (0.5 + self.power) * (1.0 + 3.0 * self.bolts.flash())
        self.place_light(GL_LIGHT3, self.bone_point("staff", self.model.crystal_center), self.crystal_light, strength)
        self.place_light(GL_LIGHT4, self.bone_point("hand_l", self.model.orb_center()), self.hand_light,
                         0.3 + 1.2 * self.power)
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
        self.draw(*self.cloth_skin.arrays())
        self.draw(*self.body_skin.arrays())
        self.draw(*self.staff_skin.arrays())
        self.draw(*self.hair_skin.arrays())
        self.draw_glowing(self.eye_skin, model.eye_color, self.eye_glow)
        self.draw_glowing(self.crystal_skin, model.crystal_color,
                          self.crystal_glow * self.pulse() * (0.6 + self.power) * (1.0 + 1.5 * self.bolts.flash()))
        self.draw_glowing(self.orb_skin, model.orb_color, self.orb_glow * (0.3 + self.power))
        self.bolts.render()
        self.end()
