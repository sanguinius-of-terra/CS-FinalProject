# database.py
# ──────────────────────────────────────────────
#  All MySQL operations:
#   • list_simulations()
#   • load_simulation(sim_id) → (sim_info, [RigidBody])
#   • save_simulation(name, bodies, gravity)
# ──────────────────────────────────────────────

from typing import List, Tuple, Dict, Any, Optional
import mysql.connector

from config    import DB_CONFIG
from vector2   import Vector2
from rigidbody import RigidBody


def _get_connection():
    return mysql.connector.connect(**DB_CONFIG, use_pure=True)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert '#RRGGBB' → (R, G, B)."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _row_to_body(row: Dict[str, Any]) -> RigidBody:
    """Convert one database row dict into a RigidBody instance."""
    shape = row["shape"]
    return RigidBody(
        label          = row["label"],
        shape          = shape,
        mass           = float(row["mass"]),
        restitution    = float(row["restitution"]),
        friction_coeff = float(row["friction_coeff"]),
        position       = Vector2(float(row["pos_x"]), float(row["pos_y"])),
        velocity       = Vector2(float(row["vel_x"]), float(row["vel_y"])),
        radius         = float(row["radius"])  if row["radius"]  is not None else 25.0,
        width          = float(row["width"])   if row["width"]   is not None else 50.0,
        height         = float(row["height"])  if row["height"]  is not None else 50.0,
        color          = row["color"] or "#FFFFFF",
        is_static      = bool(row["is_static"]),
        body_id        = int(row["id"]),
    )


# ── Public API ───────────────────────────────────────────────────────────────

def list_simulations() -> List[Dict[str, Any]]:
    """Return a list of all simulations: [{id, name, gravity, description}, ...]"""
    conn = _get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, name, gravity, description, created_at "
        "FROM simulations ORDER BY id"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def load_simulation(sim_id: int) -> Tuple[Dict[str, Any], List[RigidBody]]:
    """
    Load a simulation preset from MySQL.

    Returns
    -------
    sim_info : dict  — {id, name, gravity, description}
    bodies   : list  — list of RigidBody objects
    """
    conn = _get_connection()
    cur  = conn.cursor(dictionary=True)

    # Simulation metadata
    cur.execute("SELECT * FROM simulations WHERE id = %s", (sim_id,))
    sim_info = cur.fetchone()
    if sim_info is None:
        cur.close()
        conn.close()
        raise ValueError(f"No simulation found with id={sim_id}")

    # Objects
    cur.execute(
        "SELECT * FROM objects WHERE simulation_id = %s ORDER BY id",
        (sim_id,)
    )
    rows   = cur.fetchall()
    bodies = [_row_to_body(row) for row in rows]

    cur.close()
    conn.close()
    return sim_info, bodies


def save_simulation(
    name:    str,
    bodies:  List[RigidBody],
    gravity: float = 980.0,
    description: str = "",
) -> int:
    """
    Persist a new simulation preset to MySQL.

    Returns the new simulation id.
    """
    conn = _get_connection()
    cur  = conn.cursor()

    cur.execute(
        "INSERT INTO simulations (name, gravity, description) VALUES (%s, %s, %s)",
        (name, gravity, description)
    )
    sim_id = cur.lastrowid

    for body in bodies:
        cur.execute(
            """
            INSERT INTO objects
                (simulation_id, label, shape, mass, restitution, friction_coeff,
                 pos_x, pos_y, vel_x, vel_y,
                 radius, width, height, color, is_static)
            VALUES
                (%s, %s, %s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s, %s, %s, %s)
            """,
            (
                sim_id,
                body.label, body.shape,
                body.mass if not body.is_static else 0.0,
                body.restitution, body.friction_coeff,
                body.position.x, body.position.y,
                body.velocity.x, body.velocity.y,
                body.radius, body.width, body.height,
                body.color, body.is_static,
            )
        )

    conn.commit()
    cur.close()
    conn.close()
    return sim_id


def delete_simulation(sim_id: int):
    """Delete a simulation and all its objects (CASCADE handles the objects)."""
    conn = _get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM simulations WHERE id = %s", (sim_id,))
    conn.commit()
    cur.close()
    conn.close()
