"""Pygame GUI with two pages.

Everything is driven by buttons; the only keys are the arrow keys that move you in Player vs AI.

Level selector: one level at a time in the center, starting at level 1, with arrow buttons for the
previous / next level. Then the Watch AI or Player vs AI button.

Game page: sidebar on the left (stats box, settings pickers, control buttons), board(s) on the right.
Two modes (chosen on the level selector), Quit goes back to the level selector:
- Watch AI: Solve = solve + play, Reset.
- Player vs AI: the level twice side by side, you on the left, the AI on the right. Each legal
  arrow-key move you make, the AI plays its next planned move. Undo, Restart = restart both boards."""
import pygame

from . import bridge
from .level import LEVELS_DIR, ROOT, parse, step

ASSETS = ROOT / "assets"
TILE = 48
SIDE = 300  # sidebar width
BAR = {"watch": 40, "versus": 64}  # message bar under the board(s)
LABEL_H = 40  # "You" / "AI" score line above the boards in versus mode
GAP = 24  # space around the two boards in versus mode
PAD = 14
ROW = 24
HEAD = 22  # heading above a picker row
BTN_H = 40
SEG_H = 32  # picker (segmented) buttons
COLOR = {"bg": (30, 30, 36), "goal": (220, 180, 60), "box_on_goal": (90, 200, 90),
         "text": (230, 230, 230), "muted": (150, 150, 162), "side": (22, 22, 27),
         "panel": (42, 42, 50), "button": (60, 60, 74), "hover": (82, 82, 100),
         "accent": (80, 140, 230), "accent_hover": (105, 160, 240), "danger": (225, 85, 85)}
STEP = pygame.USEREVENT
# Engine failure reasons (Stats cost) in plain words
GAVE_UP = {"no_solution": "No solution", "node_limit": "Gave up (too many states)",
           "timeout": "Gave up (time limit)"}
ALGOS = {"astar": "A*", "greedy": "Greedy", "ucs": "UCS", "bfs": "BFS", "ids": "IDS"}
HEURS = ["h_sum", "h_match"]
USES_HEUR = {"astar", "greedy"}  # the engine ignores the heuristic for the other algorithms
MOVE_KEYS = {pygame.K_UP: "u", pygame.K_DOWN: "d", pygame.K_LEFT: "l", pygame.K_RIGHT: "r"}
STATUS_COLOR = {"Solved!": "box_on_goal", "Finished": "box_on_goal", "Playing": "accent",
                "Your move": "accent", "Solving...": "goal", "AI thinking...": "goal",
                "AI finishing...": "goal", "Error": "danger"}
N_STATS = 7  # rows in the stats box, see stat_rows() / versus_rows()
STATS_TOP = 78  # title, level name and setup line above the rows
STATS_BOX = pygame.Rect(PAD, PAD, SIDE - 2 * PAD, 2 * PAD + STATS_TOP + N_STATS * ROW)
# Level selector layout
MENU_W = 800
CARD = pygame.Rect((MENU_W - 520) // 2, 116, 520, 400)  # the level shown in the center
PREVIEW = (CARD.w - 2 * PAD - 20, 300)  # preview image fits in this box at the top of the card
ARROW = 60  # prev / next buttons beside the card


def load_sprite(name, size):
    """Load assets/<name> scaled to fit a size x size square."""
    img = pygame.image.load(ASSETS / name).convert_alpha()
    scale = size / max(img.get_size())
    return pygame.transform.smoothscale(img, (round(img.get_width() * scale), round(img.get_height() * scale)))


class Button:
    """label may be a function (label changes with the mode). selected/enabled are optional functions."""

    def __init__(self, label, rect, action, primary=False, selected=None, enabled=None, small=False):
        self.label, self.rect, self.action, self.primary = label, pygame.Rect(rect), action, primary
        self.selected, self.enabled, self.small = selected, enabled, small

    def text(self):
        return self.label() if callable(self.label) else self.label

    def is_selected(self):
        return self.selected is not None and self.selected()

    def is_enabled(self):
        return self.enabled is None or self.enabled()


class Board:
    """One copy of the level: where the boxes and the agent are, plus the score so far."""

    def __init__(self, boxes, agent):
        self.boxes, self.agent, self.moves, self.pushes = boxes, agent, 0, 0

    def snapshot(self):
        return self.boxes, self.agent, self.moves, self.pushes

    def restore(self, snap):
        self.boxes, self.agent, self.moves, self.pushes = snap

    def move(self, walls, m):
        """Apply one move with step(). Raises ValueError if illegal, and then nothing changes."""
        boxes, self.agent = step(walls, self.boxes, self.agent, m)
        self.pushes += boxes != self.boxes  # a push is a move that changed the boxes
        self.boxes = boxes
        self.moves += 1


def run():
    pygame.init()
    levels = sorted(LEVELS_DIR.glob("*.txt"))
    if not levels:
        raise SystemExit(f"no levels in {LEVELS_DIR}")
    App(levels).loop()


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 'es' if word.endswith(('sh', 'x')) else 's'}"


def segments(n, x, y, w, h, gap=6):
    """n equal rects side by side filling width w."""
    bw = (w - gap * (n - 1)) / n
    return [(round(x + i * (bw + gap)), y, round(bw), h) for i in range(n)]


class App:
    def __init__(self, levels):
        self.levels, self.idx = levels, 0
        self.mode, self.algo, self.heur, self.prune = "watch", "astar", "h_match", True
        self.plan, self.stats, self.fail, self.dead = [], None, None, None
        self.font = pygame.font.SysFont(None, 24)
        self.big = pygame.font.SysFont(None, 30)
        self.title = pygame.font.SysFont(None, 48)
        self.small = pygame.font.SysFont(None, 20)
        self.build_sidebar()
        self.build_menu()
        self.open_menu()  # opens the window, which convert_alpha() in load_sprite needs
        self.wall = load_sprite("wall.png", TILE)
        self.crate = load_sprite("crate.png", TILE - 6)
        self.crate_on_goal = self.crate.copy()  # no asset for this: tint the crate green
        self.crate_on_goal.fill((150, 230, 150), special_flags=pygame.BLEND_RGB_MULT)
        pygame.draw.rect(self.crate_on_goal, COLOR["box_on_goal"], self.crate_on_goal.get_rect(), 3, border_radius=3)
        self.player = load_sprite("player.png", TILE - 6)
        self.previews = [self.make_preview(level) for level in levels]
        self.box_counts = [len(parse(level.read_text())[2]) for level in levels]

    def build_sidebar(self):
        """Lay out the headings and buttons under the stats box, top to bottom."""
        w = SIDE - 2 * PAD
        self.headings, self.buttons = [], []
        y = STATS_BOX.bottom + PAD

        def heading(label, x=PAD):
            self.headings.append((label, (x, y)))

        heading("Algorithm")
        y += HEAD
        for (algo, label), r in zip(ALGOS.items(), segments(len(ALGOS), PAD, y, w, SEG_H, gap=4)):
            self.buttons.append(Button(label, r, lambda a=algo: self.pick(algo=a),
                                       selected=lambda a=algo: self.algo == a, small=True))
        y += SEG_H + PAD

        hw = (w - PAD) * 3 // 5  # heuristic gets more room than pruning, its labels are longer
        heading("Heuristic")
        heading("Pruning", PAD + hw + PAD)
        y += HEAD
        uses_heur = lambda: self.algo in USES_HEUR
        for heur, r in zip(HEURS, segments(len(HEURS), PAD, y, hw, SEG_H, gap=4)):
            self.buttons.append(Button(heur, r, lambda h=heur: self.pick(heur=h), small=True,
                                       selected=lambda h=heur: self.heur == h and uses_heur(), enabled=uses_heur))
        for (label, prune), r in zip([("On", True), ("Off", False)], segments(2, PAD + hw + PAD, y, w - hw - PAD, SEG_H, gap=4)):
            self.buttons.append(Button(label, r, lambda p=prune: self.pick(prune=p), small=True,
                                       selected=lambda p=prune: self.prune == p))
        y += SEG_H + 2 * PAD

        heading("Controls")
        y += HEAD
        versus = lambda: self.mode == "versus"
        self.buttons += [
            Button(lambda: "Undo" if versus() else "Solve", (PAD, y, w, BTN_H),
                   lambda: self.undo() if versus() else self.solve(), primary=True),
            Button(lambda: "Restart" if versus() else "Reset", (PAD, y + BTN_H + 10, w, BTN_H), self.reset),
            Button("Quit to levels", (PAD, y + 2 * (BTN_H + 10), w, BTN_H), self.open_menu),
        ]
        self.side_h = y + 3 * BTN_H + 2 * 10 + PAD

    # --- level selector --------------------------------------------------------

    def build_menu(self):
        """Prev / next arrows beside the center card, and the two mode buttons under it."""
        arrow_y = CARD.centery - ARROW // 2
        self.prev_btn = Button("", (CARD.x - 28 - ARROW, arrow_y, ARROW, ARROW), lambda: self.select(-1),
                               enabled=lambda: self.idx > 0)
        self.next_btn = Button("", (CARD.right + 28, arrow_y, ARROW, ARROW), lambda: self.select(1),
                               enabled=lambda: self.idx < len(self.levels) - 1)
        bw, gap, by = 210, 16, CARD.bottom + 52
        bx = (MENU_W - 2 * bw - gap) // 2
        self.menu_buttons = [
            self.prev_btn, self.next_btn,
            Button("Watch AI", (bx, by, bw, BTN_H + 4), lambda: self.start("watch"), primary=True),
            Button("Player vs AI", (bx + bw + gap, by, bw, BTN_H + 4), lambda: self.start("versus"), primary=True),
        ]
        self.menu_size = (MENU_W, by + BTN_H + 4 + 36)

    def make_preview(self, level):
        """The level's start position drawn small, to fit the top of its card."""
        walls, goals, boxes, agent = parse(level.read_text())
        surf = pygame.Surface(((max(x for x, _ in walls) + 1) * TILE, (max(y for _, y in walls) + 1) * TILE))
        surf.fill(COLOR["bg"])
        self.draw_board(surf, 0, 0, walls, goals, Board(boxes, agent))
        scale = min(PREVIEW[0] / surf.get_width(), PREVIEW[1] / surf.get_height(), 1)  # never blow up the pixel art
        return pygame.transform.smoothscale(surf, (round(surf.get_width() * scale), round(surf.get_height() * scale)))

    def open_menu(self):
        self.page = "menu"
        pygame.time.set_timer(STEP, 0)
        self.screen = pygame.display.set_mode(self.menu_size)
        pygame.display.set_caption("Sokoban — choose a level")

    def select(self, d):
        self.idx = min(max(self.idx + d, 0), len(self.levels) - 1)

    def start(self, mode):
        """Open the selected level on the game page in the chosen mode."""
        self.page, self.mode = "game", mode
        self.load()

    # --- shared actions --------------------------------------------------------

    @property
    def level(self):
        return self.levels[self.idx]

    def load(self):
        """(Re)size the window for the current level and mode, then start fresh."""
        self.reset()
        bw = (max(x for x, _ in self.walls) + 1) * TILE
        bh = self.board_h = (max(y for _, y in self.walls) + 1) * TILE
        if self.mode == "versus":
            size = (SIDE + 3 * GAP + 2 * bw, max(LABEL_H + bh + BAR["versus"], self.side_h))
        else:
            size = (SIDE + max(bw, 420), max(bh + BAR["watch"], self.side_h))
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption(f"Sokoban — {self.level.name}")
        if self.mode == "versus":
            self.new_game()

    def reset(self):
        """Put every board back at the level start. In versus mode the AI keeps its plan (R = restart)."""
        self.walls, self.goals, boxes, agent = parse(self.level.read_text())
        self.you, self.ai = Board(boxes, agent), Board(boxes, agent)
        self.history, self.finished, self.msg = [], False, ""
        pygame.time.set_timer(STEP, 0)
        if self.mode == "versus":
            self.check_deadlock()
            self.status = self.versus_status()
        else:
            self.plan, self.stats, self.fail, self.status = [], None, None, "Ready"

    def pick(self, **setting):
        """Change algo / heur / prune. Old stats would be mislabelled, so start over."""
        if all(getattr(self, k) == v for k, v in setting.items()):
            return
        for k, v in setting.items():
            setattr(self, k, v)
        if self.mode == "versus":
            self.new_game()
        else:
            self.reset()

    def setup_label(self):
        """The chosen setup, e.g. 'A* · h_match · pruning on', so every screenshot says what ran."""
        parts = [ALGOS[self.algo]] + ([self.heur] if self.algo in USES_HEUR else [])
        return " · ".join(parts + [f"pruning {'on' if self.prune else 'off'}"])

    def think(self, busy):
        """Run the engine once with the chosen settings. Returns True if it found a plan."""
        self.plan, self.stats, self.fail, self.status = [], None, None, busy
        self.draw()  # show the busy status before the (blocking) engine call
        try:
            plan, self.stats = bridge.solve(self.level, self.algo, self.heur, self.prune)
        except Exception as ex:  # show engine/bridge errors instead of crashing the GUI
            self.fail, self.msg = "Error", f"error: {ex}"
            return False
        cost = self.stats and self.stats["cost"]
        if plan is None or not isinstance(cost, int):
            self.fail = GAVE_UP.get(str(cost), "No solution")
            return False
        self.plan = plan
        return True

    def ai_step(self):
        """AI plays its next planned move (its move count is its place in the plan). False if none left."""
        if self.ai.moves >= len(self.plan):
            return False
        try:
            self.ai.move(self.walls, self.plan[self.ai.moves])
        except ValueError as ex:
            self.plan, self.fail, self.msg = [], "Error", str(ex)
            return False
        return True

    def play_step(self):
        """Timer tick: watch mode replays the plan; versus mode lets the AI finish after you solved."""
        if self.ai_step():
            return
        pygame.time.set_timer(STEP, 0)
        if self.mode == "versus":
            self.finished = True
            self.status = self.versus_status()
        elif self.status == "Playing":
            self.status = self.fail or ("Solved!" if self.ai.boxes <= self.goals else "Done")

    # --- watch mode ------------------------------------------------------------

    def solve(self):
        self.reset()  # the engine solves from the level's start position
        if self.think("Solving..."):
            self.status = "Playing"
            pygame.time.set_timer(STEP, 150)
        else:
            self.status = self.fail

    # --- player vs AI ------------------------------------------------------------

    def new_game(self):
        """Solve once with the chosen settings to get the AI's plan, then both start from the level start."""
        self.reset()
        self.think("AI thinking...")
        self.status = self.versus_status()

    def player_move(self, m):
        if self.finished or self.you.boxes == self.goals:
            return
        before = (self.you.snapshot(), self.ai.snapshot())
        try:
            self.you.move(self.walls, m)
        except ValueError:
            return  # into a wall or a blocked box: nothing counts and the AI doesn't move
        self.history.append(before)
        self.ai_step()
        self.check_deadlock()
        if self.you.boxes == self.goals:
            pygame.time.set_timer(STEP, 120)  # you're done: the AI plays out the rest of its plan
        self.status = self.versus_status()

    def undo(self):
        if not self.history:
            return
        pygame.time.set_timer(STEP, 0)
        you, ai = self.history.pop()
        self.you.restore(you)
        self.ai.restore(ai)
        self.finished = False
        self.check_deadlock()
        self.status = self.versus_status()

    def check_deadlock(self):
        """Ask the engine which of the player's boxes can never reach a goal (None = check not available)."""
        self.dead = bridge.dead_boxes(self.level, self.you.boxes)

    def versus_status(self):
        if self.finished:
            return "Finished"
        if self.you.boxes == self.goals:
            return "AI finishing..."
        if self.fail:
            return f"AI: {self.fail}"
        if self.ai.moves >= len(self.plan):
            return "AI waiting"
        return "Your move"

    def winners(self):
        """(fewest moves, fewest pushes) as 'You' / 'AI' / 'Tie' once the game is over, else None.
        An AI that couldn't solve the level loses both."""
        if not self.finished:
            return None
        ai_solved = self.ai.boxes == self.goals

        def win(you, ai):
            if not ai_solved or you < ai:
                return "You"
            return "AI" if ai < you else "Tie"

        return win(self.you.moves, self.ai.moves), win(self.you.pushes, self.ai.pushes)

    # --- main loop -----------------------------------------------------------

    def loop(self):
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                menu = self.page == "menu"
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN:  # the only keys: arrows move you in Player vs AI
                    if not menu and self.mode == "versus" and e.key in MOVE_KEYS:
                        self.player_move(MOVE_KEYS[e.key])
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.click(e.pos)
                elif e.type == STEP and not menu:
                    self.play_step()
            self.draw()
            clock.tick(60)

    def click(self, pos):
        for b in self.menu_buttons if self.page == "menu" else self.buttons:
            if b.rect.collidepoint(pos) and b.is_enabled():
                b.action()
                return

    # --- drawing -------------------------------------------------------------

    def stat_rows(self):
        """Watch mode engine stats in plain words. Cost / g(n) = box pushes; nodes = states checked."""
        s, ai = self.stats or {}, self.ai
        solved = isinstance(s.get("cost"), int)
        dash = "-"
        return [
            ("Boxes on goal", f"{len(ai.boxes & self.goals)} / {len(ai.boxes)}"),
            ("Moves used", f"{ai.moves} / {len(self.plan)}" if solved else str(ai.moves)),
            ("Box pushes", f"{ai.pushes} / {s['cost']}" if solved else str(ai.pushes)),
            ("Pushes left", str(s["cost"] - ai.pushes) if solved else dash),
            ("States checked", f"{s['nodes']:,}" if s else dash),
            ("Most waiting", f"{s['max_frontier']:,}" if s else dash),
            ("Think time", f"{s['time_ms']} ms" if s else dash),
        ]

    def versus_rows(self):
        """Player vs AI scores: (label, you, ai) rows, or (label, value) for one value."""
        s, you, ai = self.stats or {}, self.you, self.ai
        on_goal = lambda b: f"{len(b.boxes & self.goals)} / {len(b.boxes)}"
        win = self.winners()
        return [
            ("", "You", "AI"),
            ("Moves", str(you.moves), str(ai.moves)),
            ("Pushes", str(you.pushes), str(ai.pushes)),
            ("Boxes on goal", on_goal(you), on_goal(ai)),
            ("AI plan", f"{len(self.plan)} moves, {s['cost']} pushes" if self.plan else "-"),
            ("Fewest moves", win[0] if win else "-"),
            ("Fewest pushes", win[1] if win else "-"),
        ]

    def text(self, s, font, color, pos, right=False, center=False):
        img = font.render(s, True, COLOR[color])
        r = img.get_rect(midtop=pos) if center else img.get_rect(topright=pos) if right else img.get_rect(topleft=pos)
        self.screen.blit(img, r)

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, COLOR["side"], (0, 0, SIDE, self.screen.get_height()))

        box = STATS_BOX
        pygame.draw.rect(self.screen, COLOR["panel"], box, border_radius=8)
        x, rx, y = box.x + PAD, box.right - PAD, box.y + PAD
        self.text(f"Level {self.idx + 1} / {len(self.levels)}", self.big, "text", (x, y))
        status_color = STATUS_COLOR.get(self.status, "danger" if self.status.startswith("AI: ") else "muted")
        self.text(self.status, self.font, status_color, (rx, y + 4), right=True)
        self.text(self.level_name(self.idx), self.small, "muted", (x, y + 28))
        self.text(self.setup_label(), self.font, "accent", (x, y + 48))
        y += STATS_TOP
        versus = self.mode == "versus"
        for i, row in enumerate(self.versus_rows() if versus else self.stat_rows()):
            label, *values = row
            self.text(label, self.font, "muted", (x, y))
            color = "muted" if versus and i == 0 else "text"
            if len(values) == 2:  # You / AI columns
                self.text(values[0], self.font, color, (rx - 72, y), right=True)
            self.text(values[-1], self.font, color, (rx, y), right=True)
            y += ROW

        for label, pos in self.headings:
            self.text(label, self.font, "muted", pos)
        self.draw_buttons(self.buttons)

    def draw_buttons(self, buttons):
        mouse = pygame.mouse.get_pos()
        for b in buttons:
            enabled, hover = b.is_enabled(), b.rect.collidepoint(mouse)
            if not enabled:
                color = "panel"
            elif b.primary or b.is_selected():
                color = "accent_hover" if hover else "accent"
            else:
                color = "hover" if hover else "button"
            pygame.draw.rect(self.screen, COLOR[color], b.rect, border_radius=6)
            img = (self.small if b.small else self.font).render(b.text(), True, COLOR["text" if enabled else "muted"])
            self.screen.blit(img, img.get_rect(center=b.rect.center))

    def draw_board(self, surf, ox, oy, walls, goals, board, dead=()):
        """Draw a level with board's boxes and agent onto surf, top-left corner at (ox, oy)."""
        def center(cell):
            return ox + cell[0] * TILE + TILE // 2, oy + cell[1] * TILE + TILE // 2

        for cell in walls:
            surf.blit(self.wall, self.wall.get_rect(center=center(cell)))
        for cell in goals:
            pygame.draw.circle(surf, COLOR["goal"], center(cell), TILE // 6)
        for cell in board.boxes:
            img = self.crate_on_goal if cell in goals else self.crate
            surf.blit(img, img.get_rect(center=center(cell)))
            if cell in dead:
                pygame.draw.rect(surf, COLOR["danger"], img.get_rect(center=center(cell)), 3, border_radius=3)
        surf.blit(self.player, self.player.get_rect(center=center(board.agent)))

    def draw_versus(self):
        bw = (self.screen.get_width() - SIDE - 3 * GAP) // 2
        left, right = SIDE + GAP, SIDE + 2 * GAP + bw
        for ox, who, board in [(left, "You", self.you), (right, "AI", self.ai)]:
            self.text(who, self.big, "text", (ox, 12))
            score = f"{plural(board.moves, 'move')} · {plural(board.pushes, 'push')}"
            if who == "AI" and self.plan and board.moves >= len(self.plan) and not self.finished:
                score += " · done, waiting"
            self.text(score, self.font, "muted", (ox + 52, 16))
        bottom = LABEL_H + self.board_h
        pygame.draw.line(self.screen, COLOR["panel"], (right - GAP // 2, 10), (right - GAP // 2, bottom), 2)
        self.draw_board(self.screen, left, LABEL_H, self.walls, self.goals, self.you, self.dead or ())
        self.draw_board(self.screen, right, LABEL_H, self.walls, self.goals, self.ai)

        y = bottom + 14  # result / hint line, then the deadlock warning spot
        win = self.winners()
        if win:
            result = (f"Fewest moves: {win[0]} ({self.you.moves} vs {self.ai.moves})    "
                      f"Fewest pushes: {win[1]} ({self.you.pushes} vs {self.ai.pushes})")
            self.text(result, self.font, "box_on_goal", (left, y))
        else:
            self.text(self.msg or "Use the arrow keys to move", self.small, "muted", (left, y + 3))
        # Deadlock warning spot (the Prolog query plugs in via bridge.dead_boxes)
        if self.dead is None:
            self.text("Deadlock check: not connected yet", self.small, "muted", (left, y + 28))
        elif self.dead:
            self.text(f"Deadlock! {plural(len(self.dead), 'box')} can never reach a goal — press Z to undo",
                      self.font, "danger", (left, y + 26))
        else:
            self.text("Deadlock check: every box can still reach a goal", self.small, "muted", (left, y + 28))

    def level_name(self, i):
        return self.levels[i].stem.split("_", 1)[-1].replace("_", " ")

    def draw_menu(self):
        mid = MENU_W // 2
        self.text("Sokoban", self.title, "text", (mid, 28), center=True)
        self.text("Choose a level, then how to play",
                  self.small, "muted", (mid, 72), center=True)

        pygame.draw.rect(self.screen, COLOR["panel"], CARD, border_radius=12)
        area = pygame.Rect(0, CARD.y + PAD + 10, *PREVIEW)
        area.centerx = mid
        preview = self.previews[self.idx]
        self.screen.blit(preview, preview.get_rect(center=area.center))
        self.text(f"Level {self.idx + 1} · {self.level_name(self.idx)}", self.big, "text", (mid, area.bottom + 18), center=True)
        self.text(plural(self.box_counts[self.idx], "box"), self.font, "muted", (mid, area.bottom + 46), center=True)

        # one dot per level, the current one filled
        n, step_x = len(self.levels), 18
        for i in range(n):
            c = (mid - (n - 1) * step_x // 2 + i * step_x, CARD.bottom + 22)
            pygame.draw.circle(self.screen, COLOR["accent" if i == self.idx else "button"], c, 5)

        self.draw_buttons(self.menu_buttons)
        for b, d in [(self.prev_btn, -1), (self.next_btn, 1)]:  # arrow triangles on the prev / next buttons
            cx, cy = b.rect.center
            pts = [(cx + 8 * d, cy), (cx - 6 * d, cy - 12), (cx - 6 * d, cy + 12)]
            pygame.draw.polygon(self.screen, COLOR["text" if b.is_enabled() else "button"], pts)

    def draw(self):
        self.screen.fill(COLOR["bg"])
        if self.page == "menu":
            self.draw_menu()
            pygame.display.flip()
            return
        if self.mode == "versus":
            self.draw_versus()
        else:
            self.draw_board(self.screen, SIDE, 0, self.walls, self.goals, self.ai)
            self.text(self.msg, self.small, "muted", (SIDE + 10, self.screen.get_height() - BAR["watch"] + 12))
        self.draw_sidebar()
        pygame.display.flip()
