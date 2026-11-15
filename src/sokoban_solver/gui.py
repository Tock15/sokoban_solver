"""Pygame GUI. Keys: Left/Right = level, Space = solve + play, R = reset."""
import pygame

from . import bridge
from .level import LEVELS_DIR, parse, step

TILE = 48
BAR = 40
COLOR = {"bg": (30, 30, 36), "wall": (90, 90, 100), "goal": (220, 180, 60),
         "box": (170, 110, 60), "box_on_goal": (90, 170, 90), "agent": (80, 140, 230),
         "text": (230, 230, 230)}


def run():
    pygame.init()
    font = pygame.font.SysFont(None, 24)
    levels = sorted(LEVELS_DIR.glob("*.txt"))
    if not levels:
        raise SystemExit(f"no levels in {LEVELS_DIR}")
    idx, plan, status = 0, [], ""
    clock = pygame.time.Clock()
    STEP = pygame.USEREVENT

    def load(i):
        walls, goals, boxes, agent = parse(levels[i].read_text())
        w = max(x for x, _ in walls) + 1
        h = max(y for _, y in walls) + 1
        screen = pygame.display.set_mode((max(w * TILE, 480), h * TILE + BAR))
        pygame.display.set_caption(f"Sokoban — {levels[i].name}")
        return screen, walls, goals, boxes, agent

    screen, walls, goals, boxes, agent = load(idx)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_r):
                if e.key != pygame.K_r:
                    idx = (idx + (1 if e.key == pygame.K_RIGHT else -1)) % len(levels)
                screen, walls, goals, boxes, agent = load(idx)
                plan, status = [], ""
                pygame.time.set_timer(STEP, 0)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                try:
                    plan, stats = bridge.solve(levels[idx])
                    status = "no solution" if plan is None else str(stats)
                    plan = plan or []
                except Exception as ex:  # show engine/bridge errors instead of crashing the GUI
                    plan, status = [], f"error: {ex}"
                pygame.time.set_timer(STEP, 150)
            elif e.type == STEP:
                if plan:
                    try:
                        boxes, agent = step(walls, boxes, agent, plan.pop(0))
                    except ValueError as ex:
                        plan, status = [], str(ex)
                else:
                    pygame.time.set_timer(STEP, 0)

        screen.fill(COLOR["bg"])
        for (x, y) in walls:
            pygame.draw.rect(screen, COLOR["wall"], (x * TILE, y * TILE, TILE, TILE))
        for (x, y) in goals:
            pygame.draw.circle(screen, COLOR["goal"], (x * TILE + TILE // 2, y * TILE + TILE // 2), TILE // 6)
        for (x, y) in boxes:
            c = COLOR["box_on_goal"] if (x, y) in goals else COLOR["box"]
            pygame.draw.rect(screen, c, (x * TILE + 4, y * TILE + 4, TILE - 8, TILE - 8))
        ax, ay = agent
        pygame.draw.circle(screen, COLOR["agent"], (ax * TILE + TILE // 2, ay * TILE + TILE // 2), TILE // 3)
        msg = status or "Left/Right: level   Space: solve   R: reset"
        screen.blit(font.render(msg, True, COLOR["text"]), (8, screen.get_height() - BAR + 10))
        pygame.display.flip()
        clock.tick(60)
