import math


class Vector3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, factor):
        return Vector3(self.x * factor, self.y * factor, self.z * factor)

    __rmul__ = __mul__

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector3(self.y * other.z - self.z * other.y,
                       self.z * other.x - self.x * other.z,
                       self.x * other.y - self.y * other.x)

    def length(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        length = self.length()
        if length == 0.0:
            return Vector3(0.0, 0.0, 0.0)
        return self * (1.0 / length)
