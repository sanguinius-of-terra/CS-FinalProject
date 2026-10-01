-- ============================================================
--  Seed Data — three ready-to-run simulation presets
-- ============================================================
USE physics_engine;

-- -----------------------------------------------------------
-- Preset 1: "Bouncy Balls" — several circles with high restitution
-- -----------------------------------------------------------
INSERT INTO simulations (name, gravity, description) VALUES
('Bouncy Balls', 980.0, 'Multiple circles dropped at different positions with high restitution');

SET @sim1 = LAST_INSERT_ID();

INSERT INTO objects (simulation_id, label, shape, mass, restitution, friction_coeff,
                     pos_x, pos_y, vel_x, vel_y, radius, color, is_static)
VALUES
(@sim1, 'Ball A',  'circle', 1.0, 0.85, 0.2, 480, 144,  288, 0,  38, '#FF5733', FALSE),
(@sim1, 'Ball B',  'circle', 2.0, 0.75, 0.2, 960, 90,  -192, 90, 53, '#33CFFF', FALSE),
(@sim1, 'Ball C',  'circle', 0.5, 0.90, 0.1, 1440, 216, 0,   0,  27, '#AAFF33', FALSE),
(@sim1, 'Ball D',  'circle', 1.5, 0.70, 0.3, 720, 360, 144, -54, 42, '#FF33A8', FALSE),
-- static floor and ceiling
(@sim1, 'Floor',   'rect',   0.0, 0.50, 0.5, 960, 1070, 0,   0, NULL, '#555555', TRUE),
(@sim1, 'Ceiling', 'rect',   0.0, 0.50, 0.5, 960,  -10, 0,   0, NULL, '#555555', TRUE),
-- static walls
(@sim1, 'WallL',   'rect',   0.0, 0.50, 0.5,  10, 540, 0,   0, NULL, '#555555', TRUE),
(@sim1, 'WallR',   'rect',   0.0, 0.50, 0.5, 1910, 540, 0,   0, NULL, '#555555', TRUE);

-- set rect dimensions for static bodies
UPDATE objects SET width=1920, height=20 WHERE simulation_id=@sim1 AND label='Floor';
UPDATE objects SET width=1920, height=20 WHERE simulation_id=@sim1 AND label='Ceiling';
UPDATE objects SET width=20,  height=1080 WHERE simulation_id=@sim1 AND label='WallL';
UPDATE objects SET width=20,  height=1080 WHERE simulation_id=@sim1 AND label='WallR';

-- -----------------------------------------------------------
-- Preset 2: "Box Stack" — rectangles stacked, testing resting contact
-- -----------------------------------------------------------
INSERT INTO simulations (name, gravity, description) VALUES
('Box Stack', 980.0, 'Stacked boxes testing resting contact and friction');

SET @sim2 = LAST_INSERT_ID();

INSERT INTO objects (simulation_id, label, shape, mass, restitution, friction_coeff,
                     pos_x, pos_y, vel_x, vel_y, width, height, color, is_static)
VALUES
(@sim2, 'Box 1',  'rect', 2.0, 0.20, 0.6, 960, 810, 0, 0,   120, 60, '#FFC300', FALSE),
(@sim2, 'Box 2',  'rect', 1.5, 0.20, 0.6, 948, 666, 0, 0,   90, 60, '#FF5733', FALSE),
(@sim2, 'Box 3',  'rect', 1.0, 0.20, 0.6, 972, 540, 0, 0,   75, 60, '#DAF7A6', FALSE),
(@sim2, 'Slider', 'rect', 3.0, 0.10, 0.1, 240, 900, 720, 0, 105, 53, '#33CFFF', FALSE),
(@sim2, 'Floor',  'rect', 0.0, 0.30, 0.6, 960, 1070, 0, 0,  1920, 20, '#555555', TRUE),
(@sim2, 'Ceiling','rect', 0.0, 0.30, 0.6, 960,  -10, 0, 0,  1920, 20, '#555555', TRUE),
(@sim2, 'WallL',  'rect', 0.0, 0.30, 0.6,  10, 540, 0, 0,   20, 1080,'#555555', TRUE),
(@sim2, 'WallR',  'rect', 0.0, 0.30, 0.6, 1910, 540, 0, 0,   20, 1080,'#555555', TRUE);

-- -----------------------------------------------------------
-- Preset 3: "Chaos" — mixed shapes, random velocities
-- -----------------------------------------------------------
INSERT INTO simulations (name, gravity, description) VALUES
('Chaos', 980.0, 'Mixed circles and boxes flying around with random initial velocities');

SET @sim3 = LAST_INSERT_ID();

INSERT INTO objects (simulation_id, label, shape, mass, restitution, friction_coeff,
                     pos_x, pos_y, vel_x, vel_y, radius, width, height, color, is_static)
VALUES
(@sim3, 'C1', 'circle', 1.0, 0.80, 0.2, 360, 180,  480,  270, 30, NULL, NULL, '#FF5733', FALSE),
(@sim3, 'C2', 'circle', 1.5, 0.75, 0.2, 1560, 270, -360,  360, 38, NULL, NULL, '#33CFFF', FALSE),
(@sim3, 'C3', 'circle', 0.8, 0.85, 0.1, 960, 144,   120, -180, 27, NULL, NULL, '#AAFF33', FALSE),
(@sim3, 'R1', 'rect',   2.0, 0.50, 0.4, 600, 360,  240,  180, NULL, 90, 60, '#FFC300', FALSE),
(@sim3, 'R2', 'rect',   2.5, 0.40, 0.4, 1320, 450, -480,  144, NULL, 105, 75, '#FF33A8', FALSE),
(@sim3, 'R3', 'rect',   1.0, 0.60, 0.3, 960, 540,    0,  450, NULL, 68, 68, '#C0FF33', FALSE),
(@sim3, 'Floor', 'rect', 0.0, 0.40, 0.5, 960, 1070, 0, 0, NULL, 1920, 20, '#555555', TRUE),
(@sim3, 'Ceiling','rect', 0.0, 0.40, 0.5, 960,  -10, 0, 0, NULL, 1920, 20, '#555555', TRUE),
(@sim3, 'WallL', 'rect', 0.0, 0.40, 0.5,  10, 540, 0, 0, NULL,  20,1080, '#555555', TRUE),
(@sim3, 'WallR', 'rect', 0.0, 0.40, 0.5, 1910, 540, 0, 0, NULL,  20,1080, '#555555', TRUE);