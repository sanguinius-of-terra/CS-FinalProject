# main.py
# ──────────────────────────────────────────────
#  Entry point for the 2D Physics Engine.
# ──────────────────────────────────────────────

import sys
import pygame

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from config   import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, WINDOW_TITLE, MAX_DT, PHYSICS_SUBSTEPS
from database import list_simulations, load_simulation
from physics  import PhysicsWorld
from renderer import Renderer
from vector2  import Vector2

STATE_MENU    = "menu"
STATE_RUNNING = "running"


class PhysicsApp:
    def __init__(self):
        pygame.init()
        self.screen   = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock    = pygame.time.Clock()
        self.renderer = Renderer(self.screen)

        self.state          = STATE_MENU
        self.simulations    = []
        self.selected_index = 0
        self.sim_info       = {}
        self.world          = PhysicsWorld(substeps=PHYSICS_SUBSTEPS)
        self.paused         = False
        
        self.drag_enabled   = False
        self.dragged_body   = None
        self.drag_offset    = Vector2.zero()

        self._load_sim_list()

    def _load_sim_list(self):
        try:
            self.simulations = list_simulations()
        except Exception as e:
            raise RuntimeError(
                f"Could not load simulations from MySQL: {e}\n"
            ) from e

        if not self.simulations:
            print("[WARNING] No simulations found in DB. Run seed.sql first.")

    def _load_sim(self, sim_id: int):
        self.sim_info, bodies = load_simulation(sim_id)
        self.world = PhysicsWorld(gravity=float(self.sim_info["gravity"]), substeps=PHYSICS_SUBSTEPS)
        for body in bodies:
            self.world.add_body(body)
        self.paused = False

    def run(self):
        while True:
            if self.state == STATE_MENU:
                self._run_menu()
            elif self.state == STATE_RUNNING:
                self._run_simulation()

    def _run_menu(self):
        while self.state == STATE_MENU:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self._quit()
                    elif event.key == pygame.K_UP:
                        self.selected_index = max(0, self.selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = min(len(self.simulations) - 1, self.selected_index + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self.simulations:
                            sim = self.simulations[self.selected_index]
                            self._load_sim(sim["id"])
                            self.state = STATE_RUNNING

            self.renderer.draw_menu(self.simulations, self.selected_index)
            pygame.display.flip()
            self.clock.tick(FPS)

    def _run_simulation(self):
        while self.state == STATE_RUNNING:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU
                    elif event.key == pygame.K_q:
                        self._quit()
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self._load_sim(self.sim_info["id"])
                    elif event.key == pygame.K_p:
                        self.drag_enabled = not self.drag_enabled
                    elif event.key == pygame.K_v:
                        self.renderer.show_vel = not self.renderer.show_vel
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.drag_enabled:
                        mx, my = pygame.mouse.get_pos()
                        for body in reversed(self.world.bodies):
                            if body.contains(mx, my):
                                self.dragged_body = body
                                self.drag_offset = (Vector2(mx, my) - body.position).rotate(-body.angle)
                                break
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragged_body = None

            if self.dragged_body and not self.paused and dt > 0:
                mx, my = pygame.mouse.get_pos()
                target_point = Vector2(mx, my)
                world_anchor = self.dragged_body.position + self.drag_offset.rotate(self.dragged_body.angle)
                
                spring_force = (target_point - world_anchor) * 50.0
                damping = self.dragged_body.velocity * -5.0
                self.dragged_body.apply_force_at_point(spring_force + damping, world_anchor)

            if not self.paused:
                self.world.step(dt)

            self.renderer.draw(
                bodies   = self.world.bodies,
                sim_info = self.sim_info,
                fps      = self.clock.get_fps(),
                paused   = self.paused,
            )
            pygame.display.flip()

    def _quit(self):
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    try:
        app = PhysicsApp()
        app.run()
    except Exception:
        import traceback
        print("\n" + "=" * 60)
        print("The program crashed. Full error below:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        input("\nPress Enter to close this window...")
        sys.exit(1)