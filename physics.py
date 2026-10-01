# physics.py
# ──────────────────────────────────────────────
#  Core physics engine:
#   • Separating Axis Theorem (SAT)
#   • Rotational impulses & offset friction
# ──────────────────────────────────────────────

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from vector2   import Vector2
from rigidbody import RigidBody
from config    import POSITION_SLOP, POSITION_PERCENT, MAX_DT

@dataclass
class Manifold:
    a:          RigidBody
    b:          RigidBody
    normal:     Vector2 = field(default_factory=Vector2.zero)
    penetration: float  = 0.0
    contact:    Vector2 = field(default_factory=Vector2.zero)
    has_contact: bool   = False

class PhysicsWorld:
    def __init__(self, gravity: float = 980.0, substeps: int = 4):
        self.gravity   = Vector2(0, gravity)
        self.bodies:   List[RigidBody] = []
        self.substeps  = max(1, substeps)

    def add_body(self, body: RigidBody):
        self.bodies.append(body)

    def remove_body(self, body: RigidBody):
        self.bodies.remove(body)

    def clear(self):
        self.bodies.clear()

    def step(self, dt: float):
        dt = min(dt, MAX_DT)
        sub_dt = dt / self.substeps
        for _ in range(self.substeps):
            self._substep(sub_dt)

    def _substep(self, dt: float):
        for body in self.bodies:
            if not body.is_static:
                body.apply_force(self.gravity * body.mass)

        manifolds = self._detect_collisions()

        for m in manifolds:
            self._resolve_impulse(m)
        for m in manifolds:
            self._positional_correction(m)

        for body in self.bodies:
            body.integrate(dt)

    def _detect_collisions(self) -> List[Manifold]:
        manifolds = []
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = self.bodies[i], self.bodies[j]
                if a.is_static and b.is_static:
                    continue
                if not a.aabb_overlaps(b):
                    continue
                m = self._narrow_phase(a, b)
                if m and m.has_contact:
                    manifolds.append(m)
        return manifolds

    def _narrow_phase(self, a: RigidBody, b: RigidBody) -> Optional[Manifold]:
        if a.shape == "circle" and b.shape == "circle":
            return self._circle_vs_circle(a, b)
        elif a.shape == "rect" and b.shape == "rect":
            return self._poly_vs_poly(a, b)
        elif a.shape == "circle" and b.shape == "rect":
            return self._circle_vs_poly(a, b)
        elif a.shape == "rect" and b.shape == "circle":
            m = self._circle_vs_poly(b, a)
            if m and m.has_contact:
                m.normal = -m.normal
            return m
        return None

    def _circle_vs_circle(self, a: RigidBody, b: RigidBody) -> Manifold:
        m = Manifold(a, b)
        diff = b.position - a.position
        dist_sq = diff.length_sq()
        radii = a.radius + b.radius
        if dist_sq >= radii * radii:
            return m
        dist = math.sqrt(dist_sq)
        m.has_contact = True
        if dist < 1e-6:
            m.normal = Vector2(1, 0)
            m.penetration = radii
            m.contact = a.position
        else:
            m.normal = diff / dist
            m.penetration = radii - dist
            m.contact = a.position + m.normal * a.radius
        return m

    def _poly_vs_poly(self, a: RigidBody, b: RigidBody) -> Manifold:
        m = Manifold(a, b)
        verts_a = a.get_vertices()
        verts_b = b.get_vertices()
        
        axes = [
            (verts_a[1] - verts_a[0]).normalized().perpendicular(),
            (verts_a[2] - verts_a[1]).normalized().perpendicular(),
            (verts_b[1] - verts_b[0]).normalized().perpendicular(),
            (verts_b[2] - verts_b[1]).normalized().perpendicular()
        ]
        
        min_overlap = float('inf')
        smallest_axis = Vector2.zero()
        
        for axis in axes:
            min_a, max_a = self._project_vertices(verts_a, axis)
            min_b, max_b = self._project_vertices(verts_b, axis)
            overlap = min(max_a, max_b) - max(min_a, min_b)
            
            if overlap <= 0:
                return m
            if overlap < min_overlap:
                min_overlap = overlap
                smallest_axis = axis
                
        m.has_contact = True
        if (b.position - a.position).dot(smallest_axis) < 0:
            smallest_axis = -smallest_axis
            
        m.normal = smallest_axis
        m.penetration = min_overlap
        
        contacts = []
        for v in verts_a:
            if b.contains(v.x, v.y): contacts.append(v)
        for v in verts_b:
            if a.contains(v.x, v.y): contacts.append(v)
            
        if contacts:
            cx = sum(v.x for v in contacts) / len(contacts)
            cy = sum(v.y for v in contacts) / len(contacts)
            m.contact = Vector2(cx, cy)
        else:
            m.contact = a.position + (b.position - a.position) * 0.5
            
        return m

    def _circle_vs_poly(self, circle: RigidBody, poly: RigidBody) -> Manifold:
        m = Manifold(circle, poly)
        
        # Transform circle center into poly's local space for closest point calculation
        local_c = (circle.position - poly.position).rotate(-poly.angle)
        clamped_x = max(-poly.half_w, min(local_c.x, poly.half_w))
        clamped_y = max(-poly.half_h, min(local_c.y, poly.half_h))
        
        inside = False
        # If the circle's center is completely inside the rectangle bounds
        if local_c.x == clamped_x and local_c.y == clamped_y:
            inside = True
            # Force the contact point to the nearest outer edge
            if abs(poly.half_w - abs(local_c.x)) < abs(poly.half_h - abs(local_c.y)):
                clamped_x = poly.half_w if local_c.x > 0 else -poly.half_w
            else:
                clamped_y = poly.half_h if local_c.y > 0 else -poly.half_h
                
        closest_local = Vector2(clamped_x, clamped_y)
        
        # Transform the contact point back to world space
        closest_world = closest_local.rotate(poly.angle) + poly.position
        
        # Vector from the circle's center to the closest point on the polygon
        diff = closest_world - circle.position
        dist_sq = diff.length_sq()
        
        if not inside and dist_sq >= circle.radius**2:
            return m  # No contact
            
        m.has_contact = True
        dist = math.sqrt(dist_sq) if dist_sq > 1e-12 else 0.0001
        
        if inside:
            # If inside, the normal must push the circle OUT toward the nearest edge
            m.normal = -diff / dist
            m.penetration = circle.radius + dist
            m.contact = closest_world
        else:
            # If outside, the normal pushes against the outer face of the polygon
            m.normal = diff / dist
            m.penetration = circle.radius - dist
            m.contact = closest_world
            
        return m

    def _project_vertices(self, vertices: List[Vector2], axis: Vector2) -> Tuple[float, float]:
        dots = [v.dot(axis) for v in vertices]
        return min(dots), max(dots)

    def _resolve_impulse(self, m: Manifold):
        a, b = m.a, m.b
        ra = m.contact - a.position
        rb = m.contact - b.position

        va = a.velocity + Vector2(-a.angular_velocity * ra.y, a.angular_velocity * ra.x)
        vb = b.velocity + Vector2(-b.angular_velocity * rb.y, b.angular_velocity * rb.x)
        rel_vel = vb - va

        vel_along_normal = rel_vel.dot(m.normal)
        if vel_along_normal > 0:
            return

        e = min(a.restitution, b.restitution)
        ra_cross_n = ra.cross(m.normal)
        rb_cross_n = rb.cross(m.normal)

        inv_mass_sum = (a.inv_mass + b.inv_mass + 
                        (ra_cross_n**2) * a.inv_I + 
                        (rb_cross_n**2) * b.inv_I)

        j = -(1 + e) * vel_along_normal / inv_mass_sum
        impulse = m.normal * j

        a.apply_impulse(-impulse, ra)
        b.apply_impulse(impulse, rb)
        
        va_f = a.velocity + Vector2(-a.angular_velocity * ra.y, a.angular_velocity * ra.x)
        vb_f = b.velocity + Vector2(-b.angular_velocity * rb.y, b.angular_velocity * rb.x)
        rel_vel_f = vb_f - va_f
        
        tangent = rel_vel_f - m.normal * rel_vel_f.dot(m.normal)
        if tangent.length_sq() > 1e-12:
            tangent.normalize()
            ra_cross_t = ra.cross(tangent)
            rb_cross_t = rb.cross(tangent)
            
            inv_mass_sum_t = (a.inv_mass + b.inv_mass + 
                              (ra_cross_t**2) * a.inv_I + 
                              (rb_cross_t**2) * b.inv_I)
                              
            jt = -rel_vel_f.dot(tangent) / inv_mass_sum_t
            mu = (a.friction_coeff + b.friction_coeff) * 0.5
            
            friction_impulse = tangent * max(-j * mu, min(jt, j * mu))
            a.apply_impulse(-friction_impulse, ra)
            b.apply_impulse(friction_impulse, rb)

    def _positional_correction(self, m: Manifold):
        a, b = m.a, m.b
        correction_mag = max(m.penetration - POSITION_SLOP, 0.0) / (a.inv_mass + b.inv_mass) * POSITION_PERCENT
        correction = m.normal * correction_mag

        if not a.is_static:
            a.position -= correction * a.inv_mass
        if not b.is_static:
            b.position += correction * b.inv_mass