import sys
import pygame
import traceback

# Import the existing engine components
from config    import FPS
from vector2   import Vector2
from rigidbody import RigidBody
from main      import PhysicsApp, STATE_RUNNING, STATE_MENU

# 1. Dynamically add the hit-detection method to the original RigidBody class
def _body_contains(self, px: float, py: float) -> bool:
    if self.shape == "circle":
        return (self.position.x - px)**2 + (self.position.y - py)**2 <= self.radius**2
    else:
        hw, hh = self.half_w, self.half_h
        return (self.position.x - hw <= px <= self.position.x + hw) and \
               (self.position.y - hh <= py <= self.position.y + hh)

RigidBody.contains = _body_contains

# 2. Subclass PhysicsApp to inject the new event handling and logic
class DraggablePhysicsApp(PhysicsApp):
    def __init__(self):
        super().__init__()
        self.drag_enabled = False
        self.dragged_body = None

    # Override the simulation loop entirely
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
                    elif event.key == pygame.K_p:  # Changed from K_d to K_p here
                        self.drag_enabled = not self.drag_enabled
                    elif event.key == pygame.K_v:
                        self.renderer.show_vel = not self.renderer.show_vel

                # Inject mouse controls
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.drag_enabled:
                        mx, my = pygame.mouse.get_pos()
                        for body in reversed(self.world.bodies):
                            if body.contains(mx, my):
                                self.dragged_body = body
                                break
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragged_body = None

            # Apply velocity override before physics step
            if self.dragged_body and not self.paused and dt > 0:
                mx, my = pygame.mouse.get_pos()
                target = Vector2(mx, my)
                self.dragged_body.velocity = (target - self.dragged_body.position) / dt

            if not self.paused:
                self.world.step(dt)

            self.renderer.draw(
                bodies   = self.world.bodies,
                sim_info = self.sim_info,
                fps      = self.clock.get_fps(),
                paused   = self.paused,
            )
            pygame.display.flip()

# 3. Launch the extended application
if __name__ == "__main__":
    try:
        app = DraggablePhysicsApp()
        app.run()
    except Exception:
        print("\n" + "=" * 60)
        print("The program crashed. Full error below:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        input("\nPress Enter to close this window...")
        sys.exit(1)