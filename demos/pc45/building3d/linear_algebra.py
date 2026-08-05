import math


class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def added_to(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def subtracted_by(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scaled_by(self, factor):
        return Vector3(self.x * factor, self.y * factor, self.z * factor)

    def dot_product_with(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross_product_with(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def magnitude(self):
        return math.sqrt(self.dot_product_with(self))

    def normalized(self):
        length = self.magnitude()
        if length == 0.0:
            return Vector3(0.0, 0.0, 0.0)
        return self.scaled_by(1.0 / length)


def clamp_value(value, minimum, maximum):
    return max(minimum, min(maximum, value))
