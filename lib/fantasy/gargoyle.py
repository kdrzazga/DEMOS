import math

import numpy

from lib.fantasy.demon import Demon, DemonModel
from lib.fantasy.rig import both_sides
from lib.fantasy.vampire import PointedEars


class GargoyleModel(PointedEars, DemonModel):

    def __init__(self, shade="grey"):
        self.shade = shade
        super().__init__()

    def configure(self):
        super().configure()
        palettes = {"grey": ((0.44, 0.47, 0.50), (0.27, 0.29, 0.32), (0.40, 0.43, 0.47)),
                    "light grey": ((0.68, 0.70, 0.72), (0.47, 0.49, 0.52), (0.62, 0.64, 0.67)),
                    "brown": ((0.48, 0.38, 0.29), (0.30, 0.22, 0.16), (0.43, 0.34, 0.26))}
        stone, dark_stone, membrane = (numpy.asarray(color) for color in palettes[self.shade])
        self.skin = tuple(stone)
        self.dark_skin = tuple(dark_stone)
        self.membrane = tuple(membrane)
        self.horn_base = tuple(dark_stone)
        self.horn_tip = tuple(dark_stone * 0.7)
        self.spike_color = tuple(dark_stone * 0.85)
        self.claw = tuple(dark_stone * 0.6)
        self.teeth = tuple(stone * 1.15)
        self.eye_color = (1.0, 0.92, 0.25)
        self.mouth_color = tuple(dark_stone * 0.4)
        self.ear_inside = tuple(dark_stone)
        self.ear_base = (0.07, 1.845, -0.01)
        self.ear_tip = (0.21, 1.965, -0.07)
        self.ear_facing = (0.45, 0.1, 1.0)
        self.ear_width = 0.038
        self.ear_cup = 0.012
        self.ear_thickness = 0.004
        self.ear_rows = 14
        self.ear_columns = 11
        self.horns = ((((0.035, 1.895, 0.045), (0.05, 1.95, 0.0), (0.062, 1.975, -0.06), (0.066, 1.955, -0.12)),
                       0.024, 7, None),)
        self.has_tail = False
        self.wing_scale = 0.18
        self.speckle_strength = 0.22
        self.crack_darkening = 0.35
        self.crack_width = 0.012

    def build(self):
        super().build()
        self.weather(self.body)
        self.weather(self.wings)

    def build_head(self):
        super().build_head()
        self.use_bones("head")
        for side in (1.0, -1.0):
            self.build_ear(side)
        self.use_bones("head", "jaw")

    def weather(self, part):
        positions, _, colors, _ = part
        x, y, z = positions[:, 0] * 90.0, positions[:, 1] * 90.0, positions[:, 2] * 90.0
        speckle = (numpy.sin(x * 1.7 + y * 0.9) * numpy.sin(y * 2.3 - z * 1.1) * numpy.sin(z * 1.9 + x * 1.3))
        x, y, z = positions[:, 0], positions[:, 1], positions[:, 2]
        crack_field = numpy.sin(x * 23.0 + 9.0 * numpy.sin(y * 7.0)) + numpy.sin(y * 19.0 - z * 13.0 + 3.0 * numpy.sin(x * 11.0))
        crack = numpy.exp(-(crack_field / (self.crack_width * 20.0)) ** 2)
        shade = (1.0 + self.speckle_strength * speckle) * (1.0 - self.crack_darkening * crack)
        colors *= shade[:, None].astype(numpy.float32)


class Gargoyle(Demon):

    def __init__(self, height, model=None):
        self.perch = {"chest": (32.0, 0.0, 0.0), "head": (-32.0, 0.0, 0.0)}
        both_sides(self.perch, "thigh", -74.0, 22.0)
        both_sides(self.perch, "shin", 50.0)
        both_sides(self.perch, "foot", -30.0)
        both_sides(self.perch, "upper_arm", -40.0, 0.0, -20.0)
        both_sides(self.perch, "forearm", 0.0)
        both_sides(self.perch, "hand", 0.0)
        self.settled = False
        self.claw_overhang = 0.03
        self.perch_contact_band = 0.06
        self.perched_wing_fold = 30.0
        self.perched_wing_sweep = 55.0
        self.wing_spread = 0.0
        super().__init__(height, model or GargoyleModel())
        self.acting = False
        self.flapping = False
        self.hover_fraction = 0.0
        self.mouth_glow = 0.0
        self.eye_glow = 0.9
        self.skin_specular = (0.06, 0.06, 0.06, 1.0)
        self.skin_shininess = 6.0
        self.pose()

    def restart(self):
        self.settled = False
        super().restart()

    def spread_wings(self, spread):
        self.wing_spread = spread
        self.settled = False
        self.pose()

    def perch_angles(self):
        return dict(self.perch)

    def pose(self):
        if self.settled and not self.acting and not self.talking:
            return
        self.pose_wings()
        if self.acting:
            angles, self.advance = self.choreography.pose_at(self.act_seconds)
        else:
            angles, self.advance = self.perch_angles(), 0.0
        if self.talking:
            angles["jaw"] = (self.model.jaw.max_degrees * self.speech.openness(self.seconds), 0.0, 0.0)
        matrices = self.model.skeleton.matrices(angles, (0.0, 0.0, self.advance))
        self.matrices = matrices
        self.body_skin.deform(matrices)
        self.eye_skin.deform(matrices)
        self.mouth_skin.deform(matrices)
        self.wing_skin.deform(matrices, self.wing_positions, self.wing_normals)
        self.ground = self.body_skin.lowest()
        self.settled = not self.acting

    def pose_wings(self):
        super().pose_wings()
        if self.acting:
            return
        model = self.model
        folded = 1.0 - self.wing_spread
        angles = model.wing_sides * math.radians(self.perched_wing_fold * folded) * model.wing_weights
        cosines, sines = numpy.cos(angles), numpy.sin(angles)
        offset_x = self.wing_positions[:, 0] - model.wing_pivots[:, 0]
        offset_y = self.wing_positions[:, 1] - model.wing_pivots[:, 1]
        self.wing_positions[:, 0] = model.wing_pivots[:, 0] + offset_x * cosines - offset_y * sines
        self.wing_positions[:, 1] = model.wing_pivots[:, 1] + offset_x * sines + offset_y * cosines
        normal_x, normal_y = self.wing_normals[:, 0].copy(), self.wing_normals[:, 1].copy()
        self.wing_normals[:, 0] = normal_x * cosines - normal_y * sines
        self.wing_normals[:, 1] = normal_x * sines + normal_y * cosines
        sides = model.wing_sides
        sweep = math.radians(self.perched_wing_sweep * folded) * model.wing_weights
        cosines, sines = numpy.cos(sweep), numpy.sin(sweep)
        shoulder_z = model.wing_shoulder[2]
        offset_x = self.wing_positions[:, 0] - model.wing_pivots[:, 0]
        offset_z = self.wing_positions[:, 2] - shoulder_z
        self.wing_positions[:, 0] = model.wing_pivots[:, 0] + offset_x * cosines + sides * offset_z * sines
        self.wing_positions[:, 2] = shoulder_z - sides * offset_x * sines + offset_z * cosines
        normal_x, normal_z = self.wing_normals[:, 0].copy(), self.wing_normals[:, 2].copy()
        self.wing_normals[:, 0] = normal_x * cosines + sides * normal_z * sines
        self.wing_normals[:, 2] = -sides * normal_x * sines + normal_z * cosines

    def front_reach(self):
        positions = self.body_skin.positions
        touching = positions[:, 1] < self.ground + self.perch_contact_band
        return float(positions[touching, 2].max()) * self.scale()

    def perch_on(self, stool):
        self.acting = False
        self.settled = False
        self.pose()
        self.yaw = stool.yaw
        reach = stool.seat_depth - self.front_reach() + self.claw_overhang
        back_x, back_z = stool.back_center
        self.position = (back_x + reach * numpy.sin(stool.yaw), stool.floor + stool.seat_height,
                         back_z + reach * numpy.cos(stool.yaw))
