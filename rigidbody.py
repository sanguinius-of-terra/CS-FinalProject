# rigidbody.py
# ──────────────────────────────────────────────
#  Represents a single physics object.
#  Supports full rotation and angular momentum.
# ──────────────────────────────────────────────

from vector2 import Vector2
import math

class RigidBody:
    def __init__(
        self, label="body", shape="circle", mass=1.0, restitution=0.6, friction_coeff=0.3,
        position=None, velocity=None, radius=25.0, width=50.0, height=50.0,
        color="#FFFFFF", is_static=False, body_id=-1, angle=0.0
    ):
        self.label, self.shape, self.color = label, shape, color
        self.restitution, self.friction_coeff = restitution, friction_coeff
        self.is_static, self.body_id = is_static, body_id
        
        self.mass = mass if not is_static else float("inf")
        self.inv_mass = 0.0 if is_static else (1.0 / mass if mass > 0 else 0.0)
        
        self.position = position.copy() if position else Vector2(0, 0)
        self.velocity = velocity.copy() if velocity else Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        
        # Rotational Properties
        self.angle = angle
        self.angular_velocity = 0.0
        self.angular_acceleration = 0.0
        
        self.radius, self.width, self.height = radius, width, height
        
        # Moment of Inertia
        if self.is_static:
            self.I = float("inf")
            self.inv_I = 0.0
        else:
            if self.shape == "circle":
                self.I = 0.5 * self.mass * self.radius**2
            else:
                self.I = (self.mass * (self.width**2 + self.height**2)) / 12.0
            self.inv_I = 1.0 / self.I if self.I > 0 else 0.0

        self._force = Vector2(0, 0)
        self._torque = 0.0

    def apply_force(self, force: Vector2):
        if not self.is_static: 
            self._force += force

    def apply_force_at_point(self, force: Vector2, point: Vector2):
        if self.is_static: return
        self._force += force
        r = point - self.position
        self._torque += r.cross(force)
        
    def apply_impulse(self, impulse: Vector2, contact_vector: Vector2):
        if self.is_static: return
        self.velocity += impulse * self.inv_mass
        self.angular_velocity += contact_vector.cross(impulse) * self.inv_I

    def clear_forces(self):
        self._force = Vector2(0, 0)
        self._torque = 0.0

    def integrate(self, dt: float):
        if self.is_static: return
        self.acceleration = self._force * self.inv_mass
        self.angular_acceleration = self._torque * self.inv_I
        self.velocity += self.acceleration * dt
        self.angular_velocity += self.angular_acceleration * dt
        self.position += self.velocity * dt
        self.angle += self.angular_velocity * dt
        self.clear_forces()

    def get_vertices(self) -> list:
        if self.shape == "circle": return []
        hw, hh = self.width / 2, self.height / 2
        local_verts = [Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh), Vector2(-hw, hh)]
        return [v.rotate(self.angle) + self.position for v in local_verts]

    def aabb(self):
        if self.shape == "circle":
            return (self.position.x - self.radius, self.position.y - self.radius,
                    self.position.x + self.radius, self.position.y + self.radius)
        else:
            verts = self.get_vertices()
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            return (min(xs), min(ys), max(xs), max(ys))

    def aabb_overlaps(self, other: "RigidBody") -> bool:
        ax1, ay1, ax2, ay2 = self.aabb()
        bx1, by1, bx2, by2 = other.aabb()
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1
        
    def contains(self, px: float, py: float) -> bool:
        if self.shape == "circle":
            return (self.position.x - px)**2 + (self.position.y - py)**2 <= self.radius**2
        else:
            local_p = (Vector2(px, py) - self.position).rotate(-self.angle)
            hw, hh = self.width / 2, self.height / 2
            return -hw <= local_p.x <= hw and -hh <= local_p.y <= hh

    @property
    def half_w(self): return self.width / 2
    @property
    def half_h(self): return self.height / 2

    def __repr__(self):
        return f"RigidBody({self.label!r}, shape={self.shape}, pos={self.position})"