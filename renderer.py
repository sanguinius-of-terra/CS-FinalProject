# renderer.py
# ──────────────────────────────────────────────
#  Pygame rendering layer.
#  Draws every RigidBody and an on-screen HUD.
# ──────────────────────────────────────────────

import pygame
import pygame.gfxdraw
from typing import List, Dict, Any

from rigidbody import RigidBody
from vector2 import Vector2
from config    import WINDOW_WIDTH, WINDOW_HEIGHT

BG_COLOR      = (15, 15, 25)
HUD_BG        = (25, 25, 40, 180)
TEXT_COLOR    = (220, 220, 255)
ACCENT_COLOR  = (80, 200, 255)
STATIC_TINT   = (100, 100, 120)
VELOCITY_COLOR= (255, 220, 50)
NORMAL_COLOR  = (255, 80, 80)


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (200, 200, 200)


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen      = screen
        self.font_sm     = pygame.font.SysFont("monospace", 13)
        self.font_md     = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_lg     = pygame.font.SysFont("monospace", 22, bold=True)
        self.show_debug  = False
        self.show_vel    = False

    def draw(
        self,
        bodies:   List[RigidBody],
        sim_info: Dict[str, Any],
        fps:      float,
        paused:   bool,
    ):
        self.screen.fill(BG_COLOR)
        self._draw_grid()

        for body in bodies:
            self._draw_body(body)
            if self.show_debug:
                self._draw_aabb(body)
            if self.show_vel and not body.is_static:
                self._draw_velocity_arrow(body)

        self._draw_hud(sim_info, fps, paused, len(bodies))

    def _draw_grid(self):
        grid_color = (30, 30, 48)
        step = 40
        for x in range(0, WINDOW_WIDTH, step):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, step):
            pygame.draw.line(self.screen, grid_color, (0, y), (WINDOW_WIDTH, y))

    def _draw_body(self, body: RigidBody):
        color = _hex_to_rgb(body.color)
        if body.is_static:
            color = tuple(int(c * 0.7) for c in color)

        if body.shape == "circle":
            cx, cy = int(body.position.x), int(body.position.y)
            r = max(1, int(body.radius))
            pygame.gfxdraw.filled_circle(self.screen, cx, cy, r, color)
            pygame.gfxdraw.aacircle(self.screen, cx, cy, r, color)
            
            line_end = body.position + Vector2(r, 0).rotate(body.angle)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy), (int(line_end.x), int(line_end.y)), 2)
            
            rim = tuple(min(255, c + 60) for c in color)
            pygame.gfxdraw.aacircle(self.screen, cx, cy, r, rim)
        else:
            verts = [(int(v.x), int(v.y)) for v in body.get_vertices()]
            pygame.draw.polygon(self.screen, color, verts)
            rim = tuple(min(255, c + 60) for c in color)
            pygame.draw.polygon(self.screen, rim, verts, 2)

        if body.label and not body.is_static:
            surf = self.font_sm.render(body.label, True, TEXT_COLOR)
            self.screen.blit(surf, (int(body.position.x) - surf.get_width() // 2, int(body.position.y) - 8))

    def _draw_aabb(self, body: RigidBody):
        x1, y1, x2, y2 = body.aabb()
        rect = pygame.Rect(x1, y1, x2 - x1, y2 - y1)
        pygame.draw.rect(self.screen, (80, 255, 80), rect, 1)

    def _draw_velocity_arrow(self, body: RigidBody):
        scale  = 0.08
        ox, oy = int(body.position.x), int(body.position.y)
        ex     = int(ox + body.velocity.x * scale)
        ey     = int(oy + body.velocity.y * scale)
        if abs(ex - ox) < 2 and abs(ey - oy) < 2:
            return
        pygame.draw.line(self.screen, VELOCITY_COLOR, (ox, oy), (ex, ey), 2)
        pygame.draw.circle(self.screen, VELOCITY_COLOR, (ex, ey), 4)

    def _draw_hud(
        self,
        sim_info: Dict[str, Any],
        fps:      float,
        paused:   bool,
        n_bodies: int,
    ):
        lines = [
            f"Sim : {sim_info.get('name', '?')}",
            f"FPS : {fps:.0f}",
            f"Bodies: {n_bodies}",
            f"Gravity: {sim_info.get('gravity', 980):.0f} px/s²",
            "",
            "[SPACE]       Pause/Resume",
            "[R]           Restart",
            "[P]           Toggle Drag Mode",
            "[L-CLICK]     Drag",
            "[V]           Velocity arrows",
            "[ESC]         Menu",
        ]
        if paused:
            lines.insert(0, "⏸  PAUSED")

        padding = 10
        line_h  = 18
        box_w   = 280
        box_h   = len(lines) * line_h + padding * 2

        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((20, 20, 40, 190))
        self.screen.blit(panel, (8, 8))

        for i, line in enumerate(lines):
            color = ACCENT_COLOR if line.startswith("[") else TEXT_COLOR
            if "PAUSED" in line:
                color = (255, 200, 50)
            surf = self.font_sm.render(line, True, color)
            self.screen.blit(surf, (padding + 8, padding + 8 + i * line_h))

    def draw_menu(self, simulations, selected_index: int):
        self.screen.fill(BG_COLOR)
        self._draw_grid()

        title = self.font_lg.render("2D PHYSICS ENGINE", True, ACCENT_COLOR)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 40))

        sub = self.font_sm.render(
            "Select a simulation preset  ↑/↓  ENTER to run  Q to quit",
            True, TEXT_COLOR
        )
        self.screen.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 80))

        start_y = 130
        for i, sim in enumerate(simulations):
            bg_color = (40, 70, 120) if i == selected_index else (25, 25, 50)
            row_rect = pygame.Rect(80, start_y + i * 50, WINDOW_WIDTH - 160, 42)
            pygame.draw.rect(self.screen, bg_color, row_rect, border_radius=6)
            border = ACCENT_COLOR if i == selected_index else (60, 60, 90)
            pygame.draw.rect(self.screen, border, row_rect, 2, border_radius=6)

            name_surf = self.font_md.render(
                f"{sim['id']}. {sim['name']}", True,
                (255, 255, 255) if i == selected_index else TEXT_COLOR
            )
            self.screen.blit(name_surf, (row_rect.x + 14, row_rect.y + 4))

            desc = sim.get("description") or ""
            if desc:
                desc_surf = self.font_sm.render(desc[:70], True, (160, 160, 200))
                self.screen.blit(desc_surf, (row_rect.x + 14, row_rect.y + 24))