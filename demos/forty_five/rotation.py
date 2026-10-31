import math

import numpy as np


def rotation_x(degrees):
	angle = math.radians(degrees)
	cosine, sine = math.cos(angle), math.sin(angle)
	return np.array(((1.0, 0.0, 0.0), (0.0, cosine, -sine), (0.0, sine, cosine)))


def rotation_y(degrees):
	angle = math.radians(degrees)
	cosine, sine = math.cos(angle), math.sin(angle)
	return np.array(((cosine, 0.0, sine), (0.0, 1.0, 0.0), (-sine, 0.0, cosine)))


def rotation_z(degrees):
	angle = math.radians(degrees)
	cosine, sine = math.cos(angle), math.sin(angle)
	return np.array(((cosine, -sine, 0.0), (sine, cosine, 0.0), (0.0, 0.0, 1.0)))


def quaternion_from_matrix(rotation):
	trace = np.trace(rotation)
	if trace > 0.0:
		scale = math.sqrt(trace + 1.0) * 2.0
		return np.array((0.25 * scale,
		                 (rotation[2, 1] - rotation[1, 2]) / scale,
		                 (rotation[0, 2] - rotation[2, 0]) / scale,
		                 (rotation[1, 0] - rotation[0, 1]) / scale))
	axis = int(np.argmax(np.diag(rotation)))
	following, last = (axis + 1) % 3, (axis + 2) % 3
	scale = math.sqrt(1.0 + rotation[axis, axis] - rotation[following, following] - rotation[last, last]) * 2.0
	quaternion = np.zeros(4)
	quaternion[0] = (rotation[last, following] - rotation[following, last]) / scale
	quaternion[1 + axis] = 0.25 * scale
	quaternion[1 + following] = (rotation[following, axis] + rotation[axis, following]) / scale
	quaternion[1 + last] = (rotation[last, axis] + rotation[axis, last]) / scale
	return quaternion


def matrix_from_quaternion(quaternion):
	w, x, y, z = quaternion / np.linalg.norm(quaternion)
	return np.array((
		(1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
		(2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
		(2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
	))


def slerp_rotation(start_rotation, end_rotation, progress):
	start = quaternion_from_matrix(start_rotation)
	end = quaternion_from_matrix(end_rotation)
	dot = float(np.dot(start, end))
	if dot < 0.0:
		end, dot = -end, -dot
	if dot > 0.9995:
		return matrix_from_quaternion(start + (end - start) * progress)
	angle = math.acos(dot)
	blended = (math.sin((1.0 - progress) * angle) * start + math.sin(progress * angle) * end) / math.sin(angle)
	return matrix_from_quaternion(blended)


def transform_matrix(position, rotation):
	matrix = np.identity(4, dtype=np.float32)
	matrix[:3, :3] = rotation
	matrix[:3, 3] = position
	return matrix
