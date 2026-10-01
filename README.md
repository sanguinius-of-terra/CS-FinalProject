# 2D Physics Engine — Implementation Guide
========================================================

## Project File Structure

```
physics_engine/
│
├── schema.sql          # MySQL table definitions
├── seed.sql            # 3 sample presets, sized for a 1920x1080 window
├── requirements.txt    # Python dependencies
│
├── db_credentials.py   # YOUR MySQL login only — edit once, never touched again
├── config.py           # Window size, FPS, physics tuning (imports credentials)
├── database.py         # All MySQL read/write operations
├── vector2.py           # 2D math library
├── rigidbody.py        # Physics body class
├── physics.py          # Forces, collision detection & resolution
├── renderer.py         # Pygame drawing layer (anti-aliased)
└── main.py             # Game loop + entry point
```

---

## Step 1 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

Verify:
```bash
python -c "import pygame; import mysql.connector; print('OK')"
```

If pygame fails to build (common on very new Python versions like 3.13),
upgrade pip first and let pip pick the newest compatible pygame:
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install pygame --upgrade
```

---

## Step 2 — Set Up the MySQL Database

```bash
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql
```

Verify:
```bash
mysql -u root -p -e "USE physics_engine; SELECT id, name FROM simulations;"
```
You should see 3 rows: `Bouncy Balls`, `Box Stack`, `Chaos`.

---

## Step 3 — Set Your MySQL Password (only file you ever edit for this)

Open **`db_credentials.py`** — not `config.py` — and set:

```python
DB_USER     = "root"
DB_PASSWORD = "your_real_password"
```

This file is intentionally separate from `config.py` so that any future
update to `config.py` (new settings, bug fixes, etc.) never resets your
saved password back to a placeholder.

---

## Step 4 — Run It

```bash
python main.py
```

You should see a **1920×1080** window with a menu listing the 3 presets.

---

## Controls

| Key      | Action                        |
|----------|-------------------------------|
| ↑ / ↓   | Navigate menu                 |
| ENTER    | Load selected simulation      |
| SPACE    | Pause / Resume                |
| R        | Restart current simulation    |
| D        | Toggle AABB debug boxes       |
| V        | Toggle velocity arrows        |
| ESC      | Return to menu                |
| Q        | Quit                          |

---


## Changing the Window Size

If you want a different resolution than 1920×1080:

1. Edit `WINDOW_WIDTH` / `WINDOW_HEIGHT` in `config.py`
2. Update the floor and walls in your database to match the new edges:
   ```sql
   USE physics_engine;
   UPDATE objects SET pos_x = <new_width>/2,  pos_y = <new_height>-10, width  = <new_width>  WHERE label = 'Floor';
   UPDATE objects SET pos_x = 10,              pos_y = <new_height>/2, height = <new_height> WHERE label = 'WallL';
   UPDATE objects SET pos_x = <new_width>-10,  pos_y = <new_height>/2, height = <new_height> WHERE label = 'WallR';
   ```
3. Optionally reposition/resize the movable objects too, so they spread
   across the new canvas rather than clustering in one corner.

---

## Adding Your Own Simulation

```sql
USE physics_engine;

INSERT INTO simulations (name, gravity, description)
VALUES ('My Sim', 980.0, 'Custom setup');

SET @id = LAST_INSERT_ID();

INSERT INTO objects
    (simulation_id, label, shape, mass, restitution, friction_coeff,
     pos_x, pos_y, vel_x, vel_y, radius, width, height, color, is_static)
VALUES
    (@id, 'MyBall', 'circle', 1.0, 0.8, 0.2, 960, 200, 100, 0, 30, NULL, NULL, '#FF5733', FALSE);
```

Run it the same way as `seed.sql`:
```bash
mysql -u root -p < your_file.sql
```

No Python code changes are needed — `main.py` reads whatever's currently
in the `simulations` table and lists it in the menu automatically.

---

## How the Physics Works (Quick Reference)

### Gravity
Applied every substep: `F = mass × gravity_vector`

### Integration (Semi-implicit Euler, run `PHYSICS_SUBSTEPS` times per frame)
```
acceleration = total_force / mass
velocity    += acceleration × dt
position    += velocity     × dt
```

### Collision Detection
- **Circle vs Circle** — compare centre distance to sum of radii
- **Rect vs Rect**     — Separating Axis Theorem on both axes
- **Circle vs Rect**   — clamp circle centre to rect, measure distance

### Collision Resolution
1. **Impulse** — changes velocities based on coefficient of restitution
2. **Friction** — Coulomb friction along the contact tangent
3. **Positional correction** — gently pushes overlapping bodies apart

---

## Troubleshooting

**`Access denied for user 'root'@'localhost'`**
→ Your password in `db_credentials.py` is wrong or still the placeholder.

**Window is cropped / shows only part of the screen (Windows)**
→ Already fixed via `SetProcessDPIAware()` in `main.py`. If it still
  happens, check Windows display scaling settings.

**`'mysql' is not recognized as an internal or external command`**
→ Add MySQL's `bin` folder to your system PATH (see main setup guide).

**Objects fall through the floor**
→ Increase `PHYSICS_SUBSTEPS` in `config.py`, or lower `MAX_DT`.

**Very slow / low FPS**
→ The broad-phase is O(n²). For >50 objects, implement a spatial hash.
  Also try lowering `PHYSICS_SUBSTEPS` if your machine is slow.

**PyGame window closes for no apparent reason**
→ First, confirm that mysql-connector is working properly.
  If issue persists, try "use_pure=True" when initialising the MySQL connection.
