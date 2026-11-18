"""Pygame GUI: sidebar on the left (stats box + control buttons), board on the right.
Keys still work as shortcuts: Left/Right = level, Space = solve + play, R = reset."""
import pygame

from . import bridge
from .level import LEVELS_DIR, ROOT, parse, step

ASSETS = ROOT / "assets"
TILE = 48
SIDE = 260  # sidebar width
BAR = 40  # message bar under the board
PAD = 14
ROW = 26
BTN_H = 40
COLOR = {"bg": (30, 30, 36), "goal": (220, 180, 60), "box_on_goal": (90, 200, 90),
         "text": (230, 230, 230), "muted": (150, 150, 162), "side": (22, 22, 27),
         "panel": (42, 42, 50), "button": (60, 60, 74), "hover": (82, 82, 100),
         "accent": (80, 140, 230), "accent_hover": (105, 160, 240)}
STEP = pygame.USEREVENT
# Engine failure reasons (Stats cost) in plain words
GAVE_UP = {"no_solution": "No solution", "node_limit": "Gave up (too many states)",
           "timeout": "Gave up (time limit)"}
N_STATS = 7  # rows in the stats box, see stat_rows()
STATS_BOX = pygame.Rect(PAD, PAD, SIDE - 2 * PAD, 2 * PAD + 52 + N_STATS * ROW)
BTN_TOP = STATS_BOX.bottom + 2 * PAD + ROW  # leave room for the "Controls" heading
SIDE_H = BTN_TOP + 3 * BTN_H + 2 * 10 + PAD


def load_sprite(name, size, cut_bg=False):
    """Load assets/<name> scaled to fit a size x size square. cut_bg makes the near-white
    background transparent (only the part connected to the image edges, so whites inside stay)."""
    img = pygame.image.load(ASSETS / name).convert_alpha()
    if cut_bg:
        w, h = img.get_size()
        white = pygame.mask.from_threshold(img, (255, 255, 255, 255), (30, 30, 30, 255))
        bg = pygame.mask.Mask((w, h))
        for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
            if white.get_at(corner):
                bg.draw(white.connected_component(corner), (0, 0))
        for x in range(w):
            for y in range(h):
                if bg.get_at((x, y)):
                    img.set_at((x, y), (0, 0, 0, 0))
    scale = size / max(img.get_size())
    return pygame.transform.smoothscale(img, (round(img.get_width() * scale), round(img.get_height() * scale)))


class Button:
    def __init__(self, label, rect, action, primary=False):
        self.label, self.rect, self.action, self.primary = label, pygame.Rect(rect), action, primary


def run():
    pygame.init()
    levels = sorted(LEVELS_DIR.glob("*.txt"))
    if not levels:
        raise SystemExit(f"no levels in {LEVELS_DIR}")
    App(levels).loop()


class App:
    def __init__(self, levels):
        self.levels, self.idx = levels, 0
        self.font = pygame.font.SysFont(None, 24)
        self.big = pygame.font.SysFont(None, 30)
        self.small = pygame.font.SysFont(None, 20)
        w = SIDE - 2 * PAD
        half = (w - 10) // 2
        self.buttons = [
            Button("< Prev", (PAD, BTN_TOP, half, BTN_H), lambda: self.change_level(-1)),
            Button("Next >", (PAD + half + 10, BTN_TOP, half, BTN_H), lambda: self.change_level(1)),
            Button("Solve", (PAD, BTN_TOP + BTN_H + 10, w, BTN_H), self.solve, primary=True),
            Button("Reset", (PAD, BTN_TOP + 2 * (BTN_H + 10), w, BTN_H), self.reset),
        ]
        self.load()  # opens the window, which convert_alpha() in load_sprite needs
        self.wall = load_sprite("wall.png", TILE)
        self.crate = load_sprite("Wooden_Crate copy.png", TILE - 6)
        self.crate_on_goal = self.crate.copy()  # no asset for this: tint the crate green
        self.crate_on_goal.fill((150, 230, 150), special_flags=pygame.BLEND_RGB_MULT)
        pygame.draw.rect(self.crate_on_goal, COLOR["box_on_goal"], self.crate_on_goal.get_rect(), 3, border_radius=3)
        self.player = load_sprite("player.png", TILE - 6, cut_bg=True)

    # --- actions -------------------------------------------------------------

    def load(self):
        self.reset()
        w = max(x for x, _ in self.walls) + 1
        h = max(y for _, y in self.walls) + 1
        self.screen = pygame.display.set_mode((SIDE + max(w * TILE, 360), max(h * TILE + BAR, SIDE_H)))
        pygame.display.set_caption(f"Sokoban — {self.levels[self.idx].name}")

    def reset(self):
        self.walls, self.goals, self.boxes, self.agent = parse(self.levels[self.idx].read_text())
        self.plan, self.stats, self.status, self.msg = [], None, "Ready", ""
        self.moves = self.pushes = self.total_moves = 0
        pygame.time.set_timer(STEP, 0)

    def change_level(self, d):
        self.idx = (self.idx + d) % len(self.levels)
        self.load()

    def solve(self):
        self.reset()  # the engine solves from the level's start position
        self.status = "Solving..."
        self.draw()  # show "Solving..." before the (blocking) engine call
        try:
            plan, self.stats = bridge.solve(self.levels[self.idx])
        except Exception as ex:  # show engine/bridge errors instead of crashing the GUI
            self.status, self.msg = "Error", f"error: {ex}"
            return
        cost = self.stats and self.stats["cost"]
        if plan is None or not isinstance(cost, int):
            self.status = GAVE_UP.get(str(cost), "No solution")
            return
        self.plan, self.total_moves, self.status = plan, len(plan), "Playing"
        pygame.time.set_timer(STEP, 150)

    def play_step(self):
        if not self.plan:
            pygame.time.set_timer(STEP, 0)
            if self.status == "Playing":
                self.status = "Solved!" if self.boxes <= self.goals else "Done"
            return
        try:
            boxes, self.agent = step(self.walls, self.boxes, self.agent, self.plan.pop(0))
        except ValueError as ex:
            self.plan, self.status, self.msg = [], "Error", str(ex)
            return
        self.pushes += boxes != self.boxes
        self.boxes = boxes
        self.moves += 1

    # --- main loop -----------------------------------------------------------

    def loop(self):
        clock = pygame.time.Clock()
        keys = {pygame.K_LEFT: lambda: self.change_level(-1), pygame.K_RIGHT: lambda: self.change_level(1),
                pygame.K_SPACE: self.solve, pygame.K_r: self.reset}
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN and e.key in keys:
                    keys[e.key]()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for b in self.buttons:
                        if b.rect.collidepoint(e.pos):
                            b.action()
                            break
                elif e.type == STEP:
                    self.play_step()
            self.draw()
            clock.tick(60)

    # --- drawing -------------------------------------------------------------

    def stat_rows(self):
        """Engine stats in plain words. Cost / g(n) = box pushes; nodes = states checked."""
        s = self.stats or {}
        solved = isinstance(s.get("cost"), int)
        dash = "-"
        return [
            ("Boxes on goal", f"{len(self.boxes & self.goals)} / {len(self.boxes)}"),
            ("Moves used", f"{self.moves} / {self.total_moves}" if solved else str(self.moves)),
            ("Box pushes", f"{self.pushes} / {s['cost']}" if solved else str(self.pushes)),
            ("Pushes left", str(s["cost"] - self.pushes) if solved else dash),
            ("States checked", f"{s['nodes']:,}" if s else dash),
            ("Most waiting", f"{s['max_frontier']:,}" if s else dash),
            ("Think time", f"{s['time_ms']} ms" if s else dash),
        ]

    def text(self, s, font, color, pos, right=False):
        img = font.render(s, True, COLOR[color])
        r = img.get_rect(topright=pos) if right else img.get_rect(topleft=pos)
        self.screen.blit(img, r)

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, COLOR["side"], (0, 0, SIDE, self.screen.get_height()))

        box = STATS_BOX
        pygame.draw.rect(self.screen, COLOR["panel"], box, border_radius=8)
        x, rx, y = box.x + PAD, box.right - PAD, box.y + PAD
        self.text(f"Level {self.idx + 1} / {len(self.levels)}", self.big, "text", (x, y))
        status_color = {"Solved!": "box_on_goal", "Playing": "accent", "Solving...": "goal"}.get(self.status, "muted")
        self.text(self.status, self.font, status_color, (rx, y + 4), right=True)
        name = self.levels[self.idx].stem.split("_", 1)[-1].replace("_", " ")
        self.text(name, self.small, "muted", (x, y + 28))
        y += 52
        for label, value in self.stat_rows():
            self.text(label, self.font, "muted", (x, y))
            self.text(value, self.font, "text", (rx, y), right=True)
            y += ROW

        self.text("Controls", self.font, "muted", (PAD, box.bottom + 2 * PAD - 4))
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            hover = b.rect.collidepoint(mouse)
            color = ("accent_hover" if hover else "accent") if b.primary else ("hover" if hover else "button")
            pygame.draw.rect(self.screen, COLOR[color], b.rect, border_radius=6)
            img = self.font.render(b.label, True, COLOR["text"])
            self.screen.blit(img, img.get_rect(center=b.rect.center))

    def draw(self):
        self.screen.fill(COLOR["bg"])
        def blit_cell(img, cell):
            x, y = cell
            self.screen.blit(img, img.get_rect(center=(SIDE + x * TILE + TILE // 2, y * TILE + TILE // 2)))

        for cell in self.walls:
            blit_cell(self.wall, cell)
        for (x, y) in self.goals:
            pygame.draw.circle(self.screen, COLOR["goal"], (SIDE + x * TILE + TILE // 2, y * TILE + TILE // 2), TILE // 6)
        for cell in self.boxes:
            blit_cell(self.crate_on_goal if cell in self.goals else self.crate, cell)
        blit_cell(self.player, self.agent)
        msg = self.msg or "Keys: Left/Right level, Space solve, R reset"
        self.text(msg, self.small, "muted", (SIDE + 10, self.screen.get_height() - BAR + 12))
        self.draw_sidebar()
        pygame.display.flip()
