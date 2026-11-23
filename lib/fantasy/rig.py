import math

import numpy

from lib.animals.dragon import StatueMesh
from lib.fantasy.anatomy import smoothstep


def mirrored(point, side):
    return numpy.array((point[0] * side, point[1], point[2]), dtype=numpy.float64)


def mirrored_all(points, side):
    return [mirrored(point, side) for point in points]


def side_name(name, side):
    return name + ("_r" if side > 0.0 else "_l")


def rotation(pitch, yaw, roll):
    pitch, yaw, roll = math.radians(pitch), math.radians(yaw), math.radians(roll)
    cos_pitch, sin_pitch = math.cos(pitch), math.sin(pitch)
    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
    cos_roll, sin_roll = math.cos(roll), math.sin(roll)
    around_x = numpy.array(((1.0, 0.0, 0.0), (0.0, cos_pitch, -sin_pitch), (0.0, sin_pitch, cos_pitch)))
    around_y = numpy.array(((cos_yaw, 0.0, sin_yaw), (0.0, 1.0, 0.0), (-sin_yaw, 0.0, cos_yaw)))
    around_z = numpy.array(((cos_roll, -sin_roll, 0.0), (sin_roll, cos_roll, 0.0), (0.0, 0.0, 1.0)))
    return around_y @ around_x @ around_z


def translation(offset):
    matrix = numpy.identity(4)
    matrix[:3, 3] = offset
    return matrix


def path_distances(positions, path):
    path = numpy.asarray(path, dtype=numpy.float64)
    nearest = numpy.full(len(positions), numpy.inf)
    for start, end in zip(path[:-1], path[1:]):
        span = end - start
        fraction = numpy.clip((positions - start) @ span / max(span @ span, 1e-12), 0.0, 1.0)
        distance = numpy.linalg.norm(positions - (start + fraction[:, None] * span), axis=1)
        nearest = numpy.minimum(nearest, distance)
    return nearest


class Bone:

    def __init__(self, name, parent, path, radius, blend_radius, region=None):
        self.name = name
        self.region = region
        self.parent = parent
        self.path = numpy.asarray(path, dtype=numpy.float64)
        self.pivot = self.path[0]
        self.radius = radius
        self.blend_radius = blend_radius
        direction = self.path[1] - self.path[0]
        self.axis = direction / max(numpy.linalg.norm(direction), 1e-12)


class Skeleton:

    def __init__(self, bones):
        self.bones = bones
        self.index = {bone.name: number for number, bone in enumerate(bones)}
        self.parents = [self.index[bone.parent] if bone.parent else -1 for bone in bones]

    def label(self, positions, group):
        candidates = [self.index[name] for name in group]
        if len(candidates) == 1:
            return numpy.full(len(positions), candidates[0], dtype=numpy.int32)
        nearest = [number for number in candidates if self.bones[number].region is None] or candidates
        distances = numpy.stack([path_distances(positions, self.bones[number].path) / self.bones[number].radius
                                 for number in nearest])
        labels = numpy.asarray(nearest, dtype=numpy.int32)[distances.argmin(axis=0)]
        for number in candidates:
            region = self.bones[number].region
            if region is not None:
                labels[region.claims(positions)] = number
        return labels

    def own_weights(self, positions, bone_ids, overrides):
        weights = numpy.ones(len(positions))
        for number, bone in enumerate(self.bones):
            if self.parents[number] < 0 or bone.blend_radius <= 0.0:
                continue
            mask = bone_ids == number
            projection = (positions[mask] - bone.pivot) @ bone.axis
            weights[mask] = smoothstep(projection / bone.blend_radius)
        overridden = ~numpy.isnan(overrides)
        weights[overridden] = overrides[overridden]
        return weights

    def matrices(self, angles, root_offset):
        matrices = numpy.empty((len(self.bones), 4, 4))
        for number, bone in enumerate(self.bones):
            local = numpy.identity(4)
            local[:3, :3] = rotation(*angles.get(bone.name, (0.0, 0.0, 0.0)))
            local = translation(bone.pivot) @ local @ translation(-bone.pivot)
            parent = self.parents[number]
            matrices[number] = (translation(root_offset) @ local) if parent < 0 else matrices[parent] @ local
        return matrices


class LabeledMesh(StatueMesh):

    def __init__(self):
        super().__init__()
        self.bone_group = ()
        self.next_weights = None
        self.next_blend_target = None
        self.runs = []

    def add_vertices(self, positions, normals, colors):
        first = super().add_vertices(positions, normals, colors)
        count = self.vertex_count - first
        weights = numpy.full(count, numpy.nan) if self.next_weights is None else numpy.asarray(
            self.next_weights, dtype=numpy.float64).reshape(-1)
        self.next_weights = None
        self.runs.append((self.bone_group, count, weights, self.next_blend_target))
        self.next_blend_target = None
        return first

    def bone_labels(self, skeleton, positions):
        labels = []
        start = 0
        for group, count, _, _ in self.runs:
            labels.append(skeleton.label(positions[start:start + count].astype(numpy.float64), group))
            start += count
        overrides = numpy.concatenate([weights for _, _, weights, _ in self.runs])
        targets = numpy.concatenate([numpy.full(count, -1 if target is None else skeleton.index[target])
                                     for _, count, _, target in self.runs])
        return numpy.concatenate(labels), overrides, targets


class Skin:

    def __init__(self, arrays, labels, overrides, targets, skeleton):
        positions, normals, colors, indices = arrays
        self.skeleton = skeleton
        self.order = numpy.argsort(labels, kind="stable")
        inverse = numpy.empty_like(self.order)
        inverse[self.order] = numpy.arange(len(self.order))
        self.rest_positions = positions[self.order].astype(numpy.float64)
        self.rest_normals = normals[self.order].astype(numpy.float64)
        self.colors = numpy.ascontiguousarray(colors[self.order])
        self.indices = numpy.ascontiguousarray(inverse[indices].astype(numpy.uint32))
        bone_ids = labels[self.order]
        self.slices = []
        for number in range(len(skeleton.bones)):
            start, end = numpy.searchsorted(bone_ids, (number, number + 1))
            if end > start:
                self.slices.append((number, start, end))
        weights = skeleton.own_weights(self.rest_positions, bone_ids, overrides[self.order])
        parents = numpy.asarray(skeleton.parents)[bone_ids]
        targets = targets[self.order]
        parents = numpy.where(targets >= 0, targets, parents)
        self.blended = numpy.nonzero((weights < 0.999) & (parents >= 0))[0]
        self.blend_weights = weights[self.blended][:, None]
        self.blend_parents = parents[self.blended]
        self.positions = numpy.zeros(self.rest_positions.shape, dtype=numpy.float32)
        self.normals = numpy.zeros(self.rest_normals.shape, dtype=numpy.float32)

    def arrays(self):
        return self.positions, self.normals, self.colors, self.indices

    def lowest(self):
        return float(self.positions[:, 1].min())

    def deform(self, matrices, positions=None, normals=None):
        source = self.rest_positions if positions is None else positions[self.order]
        source_normals = self.rest_normals if normals is None else normals[self.order]
        rotations, offsets = matrices[:, :3, :3], matrices[:, :3, 3]
        for number, start, end in self.slices:
            self.positions[start:end] = source[start:end] @ rotations[number].T + offsets[number]
            self.normals[start:end] = source_normals[start:end] @ rotations[number].T
        if len(self.blended):
            parent_rotations = rotations[self.blend_parents]
            blended_source = source[self.blended]
            parent_positions = numpy.einsum("kij,kj->ki", parent_rotations, blended_source) + offsets[
                self.blend_parents]
            parent_normals = numpy.einsum("kij,kj->ki", parent_rotations, source_normals[self.blended])
            weights = self.blend_weights
            self.positions[self.blended] = weights * self.positions[self.blended] + (1.0 - weights) * parent_positions
            self.normals[self.blended] = weights * self.normals[self.blended] + (1.0 - weights) * parent_normals


def biped_skeleton(pelvis_path, chest_path, head_path, arm_paths, forearm_path, hand_path, thigh_path, shin_path,
                   foot_path,
                   radii, extra_bones=()):
    bones = [Bone("pelvis", None, pelvis_path, radii["pelvis"], 0.0),
             Bone("chest", "pelvis", chest_path, radii["chest"], radii["waist_blend"]),
             Bone("head", "chest", head_path, radii["head"], radii["neck_blend"])]
    bones.extend(extra_bones)
    for side in (1.0, -1.0):
        bones.append(Bone(side_name("upper_arm", side), "chest", mirrored_all(arm_paths, side), radii["upper_arm"],
                          radii["shoulder_blend"]))
        bones.append(Bone(side_name("forearm", side), side_name("upper_arm", side),
                          mirrored_all(forearm_path, side), radii["forearm"], radii["elbow_blend"]))
        bones.append(Bone(side_name("hand", side), side_name("forearm", side), mirrored_all(hand_path, side),
                          radii["hand"], radii["wrist_blend"]))
        bones.append(Bone(side_name("thigh", side), "pelvis", mirrored_all(thigh_path, side), radii["thigh"],
                          radii["hip_blend"]))
        bones.append(Bone(side_name("shin", side), side_name("thigh", side), mirrored_all(shin_path, side),
                          radii["shin"], radii["knee_blend"]))
        bones.append(Bone(side_name("foot", side), side_name("shin", side), mirrored_all(foot_path, side),
                          radii["foot"], radii["ankle_blend"]))
    return Skeleton(bones)


def jaw_bone(jaw, blend_radius):
    return Bone("jaw", "head", (jaw.hinge, jaw.chin), jaw.half_width, blend_radius, jaw)


def sided(pose, name, side, pitch, yaw=0.0, roll=0.0):
    pose[side_name(name, side)] = (pitch, yaw * side, roll * side)


def both_sides(pose, name, pitch, yaw=0.0, roll=0.0):
    for side in (1.0, -1.0):
        sided(pose, name, side, pitch, yaw, roll)


class Choreography:

    def __init__(self, standing_pose, stride, punching_side=1.0):
        self.standing_pose = standing_pose
        self.stride = stride
        self.punching_side = punching_side
        self.punch_lunge = 0.35 * stride
        self.keyframes = []
        self.compose()
        self.duration = self.keyframes[-1][0]

    def crouch(self):
        pose = {"chest": (25.0, 0.0, 0.0), "head": (-15.0, 0.0, 0.0)}
        both_sides(pose, "thigh", -100.0)
        both_sides(pose, "shin", 125.0)
        both_sides(pose, "foot", -25.0)
        both_sides(pose, "upper_arm", -25.0)
        both_sides(pose, "forearm", -35.0)
        return pose

    def stand(self):
        pose = {}
        both_sides(pose, "forearm", -10.0)
        return pose

    def duck(self):
        pose = {"chest": (35.0, 0.0, 0.0), "head": (-30.0, 0.0, 0.0)}
        both_sides(pose, "thigh", -75.0)
        both_sides(pose, "shin", 100.0)
        both_sides(pose, "foot", -25.0)
        both_sides(pose, "upper_arm", -75.0, -10.0)
        both_sides(pose, "forearm", -95.0)
        return pose

    def contact(self, lead):
        trail = -lead
        pose = {"chest": (4.0, 6.0 * lead, 0.0), "head": (-4.0, -6.0 * lead, 0.0)}
        sided(pose, "thigh", lead, -28.0)
        sided(pose, "shin", lead, 10.0)
        sided(pose, "foot", lead, 0.0)
        sided(pose, "thigh", trail, 18.0)
        sided(pose, "shin", trail, 25.0)
        sided(pose, "foot", trail, -12.0)
        sided(pose, "upper_arm", lead, 20.0)
        sided(pose, "upper_arm", trail, -22.0)
        both_sides(pose, "forearm", -25.0)
        return pose

    def passing(self, swing):
        stance = -swing
        pose = {"chest": (4.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0)}
        sided(pose, "thigh", swing, -25.0)
        sided(pose, "shin", swing, 60.0)
        sided(pose, "foot", swing, -10.0)
        sided(pose, "thigh", stance, 2.0)
        sided(pose, "shin", stance, 3.0)
        both_sides(pose, "upper_arm", -5.0)
        both_sides(pose, "forearm", -25.0)
        return pose

    def guard(self):
        fist, other = self.punching_side, -self.punching_side
        pose = {"chest": (5.0, 20.0 * fist, 0.0), "head": (0.0, -20.0 * fist, 0.0)}
        sided(pose, "upper_arm", fist, -25.0)
        sided(pose, "forearm", fist, -115.0)
        sided(pose, "upper_arm", other, -55.0)
        sided(pose, "forearm", other, -100.0)
        sided(pose, "thigh", other, -22.0)
        sided(pose, "shin", other, 25.0)
        sided(pose, "foot", other, -3.0)
        sided(pose, "thigh", fist, 12.0)
        sided(pose, "shin", fist, 15.0)
        sided(pose, "foot", fist, -8.0)
        return pose

    def punch(self):
        fist, other = self.punching_side, -self.punching_side
        pose = {"chest": (12.0, -28.0 * fist, 0.0), "head": (-5.0, 28.0 * fist, 0.0)}
        sided(pose, "upper_arm", fist, -98.0, 16.0)
        sided(pose, "forearm", fist, -8.0)
        sided(pose, "upper_arm", other, -45.0)
        sided(pose, "forearm", other, -105.0)
        sided(pose, "thigh", other, -32.0)
        sided(pose, "shin", other, 38.0)
        sided(pose, "foot", other, -6.0)
        sided(pose, "thigh", fist, 20.0)
        sided(pose, "shin", fist, 12.0)
        sided(pose, "foot", fist, -12.0)
        return pose

    def strike_hold_seconds(self):
        return 0.5

    def add(self, seconds, pose, advance):
        previous = self.keyframes[-1][0] if self.keyframes else 0.0
        self.keyframes.append((previous + seconds, pose, advance))

    def compose(self):
        self.strike(self.approach())

    def approach(self):
        start = -2.0 * self.stride
        self.add(0.0, self.crouch(), start)
        self.add(0.7, self.crouch(), start)
        self.add(1.1, self.stand(), start)
        self.add(0.6, self.stand(), start)
        self.add(0.35, self.duck(), start)
        self.add(0.45, self.duck(), start)
        self.add(0.5, self.stand(), start)
        self.add(0.4, self.stand(), start)
        position = start
        for lead in (1.0, -1.0, 1.0, -1.0):
            self.add(0.3, self.passing(lead), position + 0.5 * self.stride)
            position += self.stride
            self.add(0.3, self.contact(lead), position)
        self.add(0.45, self.stand(), position)
        return position

    def strike(self, position):
        self.add(0.4, self.stand(), position)
        self.add(0.55, self.guard(), position)
        self.add(0.25, self.guard(), position)
        self.add(0.14, self.punch(), position + self.punch_lunge)
        self.add(self.strike_hold_seconds(), self.punch(), position + self.punch_lunge)
        self.add(0.6, self.guard(), position)
        self.add(0.5, self.stand(), position)
        self.add(0.8, self.stand(), position)
        self.add(1.0, self.crouch(), position)
        self.add(0.5, self.crouch(), position)

    def segment(self, seconds):
        times = [time for time, _, _ in self.keyframes]
        index = min(max(numpy.searchsorted(times, seconds, side="right") - 1, 0), len(times) - 2)
        span = times[index + 1] - times[index]
        local = 0.0 if span <= 0.0 else (seconds - times[index]) / span
        return index, min(max(local, 0.0), 1.0)

    def angle(self, name, index, local):
        last = len(self.keyframes) - 1
        values = [numpy.asarray(self.keyframes[min(max(index + step, 0), last)][1].get(name, (0.0, 0.0, 0.0)))
                  for step in (-1, 0, 1, 2)]
        before, start, end, after = values
        return 0.5 * (2.0 * start + (end - before) * local
                      + (2.0 * before - 5.0 * start + 4.0 * end - after) * local ** 2
                      + (3.0 * start - before - 3.0 * end + after) * local ** 3)

    def pose_at(self, seconds):
        seconds = seconds % self.duration
        index, local = self.segment(seconds)
        names = set(self.standing_pose)
        for _, pose, _ in self.keyframes[max(index - 1, 0):index + 3]:
            names.update(pose)
        angles = {}
        for name in names:
            standing = numpy.asarray(self.standing_pose.get(name, (0.0, 0.0, 0.0)))
            angles[name] = tuple(standing + self.angle(name, index, local))
        start_advance = self.keyframes[index][2]
        end_advance = self.keyframes[index + 1][2]
        return angles, start_advance + (end_advance - start_advance) * local
