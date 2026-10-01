# vector2.py
# ──────────────────────────────────────────────
#  Lightweight 2-D vector with all operations
#  the physics engine needs.
# ──────────────────────────────────────────────

import math

class Vector2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    # ── Arithmetic ──────────────────────────────
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __imul__(self, scalar):
        self.x *= scalar
        self.y *= scalar
        return self

    # ── Comparison ──────────────────────────────
    def __eq__(self, other):
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9

    def __repr__(self):
        return f"Vector2({self.x:.3f}, {self.y:.3f})"

    # ── Core operations ─────────────────────────
    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other) -> float:
        return self.x * other.y - self.y * other.x

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.length_sq())

    def normalized(self) -> "Vector2":
        mag = self.length()
        if mag < 1e-12:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)

    def normalize(self):
        mag = self.length()
        if mag >= 1e-12:
            self.x /= mag
            self.y /= mag

    def reflect(self, normal: "Vector2") -> "Vector2":
        return self - normal * (2.0 * self.dot(normal))

    def perpendicular(self) -> "Vector2":
        return Vector2(-self.y, self.x)

    def rotate(self, angle: float) -> "Vector2":
        """Rotate this vector by the given angle in radians."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Vector2(self.x * c - self.y * s, self.x * s + self.y * c)

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)

    # ── Convenience ─────────────────────────────
    def to_tuple(self):
        return (self.x, self.y)

    def to_int_tuple(self):
        return (int(self.x), int(self.y))

    @staticmethod
    def distance(a: "Vector2", b: "Vector2") -> float:
        return (a - b).length()

    @staticmethod
    def zero() -> "Vector2":
        return Vector2(0, 0)