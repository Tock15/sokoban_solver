import math
import os

import pygame

from . import bridge, theme
from .level import LEVELS_DIR, ROOT, Board, floor, parse
from .theme import BTN_H, COLOR, GAP, PAD, SEG_H, TILE

ASSETS = ROOT / "assets"
STEP = pygame.USEREVENT
REPLAY_MS = {"watch": 150, "versus": 120}

SIDE = 320
HEADER_H = 46
FOOTER_H = {"watch": 56, "versus": 120}
ALERT = (440, 214)
WATCH_MIN_W = 420
ROW = 27
N_STATS = 7
STATS_TOP = 96
STATS_BOX = pygame.Rect(PAD, PAD, SIDE - 2 * PAD, PAD + STATS_TOP + N_STATS * ROW + 6)

MENU_W = 820
CARD = pygame.Rect((MENU_W - 540) // 2, 140, 540, 446)
INSET = pygame.Rect(CARD.x + PAD, CARD.y + PAD, CARD.w - 2 * PAD, 300)
ARROW = 56

GAVE_UP = {"no_solution": "No solution", "node_limit": "Gave up (too many states)",
           "timeout": "Gave up (time limit)"}
ALGOS = {"astar": "A*", "greedy": "Greedy", "ucs": "UCS", "bfs": "BFS", "ids": "IDS"}
HEURS = ["h_sum", "h_match"]
USES_HEUR = {"astar", "greedy"}
MOVE_KEYS = {pygame.K_UP: "u", pygame.K_DOWN: "d", pygame.K_LEFT: "l", pygame.K_RIGHT: "r"}
STATUS_COLOR = {"Solved!": "success", "Finished": "success", "Playing": "accent", "Your move": "accent",
                "Solving...": "warning", "AI thinking...": "warning", "AI finishing...": "warning"}
WINNER_COLOR = {"You": "success", "AI": "accent", "Tie": "warning"}


def load_sprite(name, size):
    img = pygame.image.load(ASSETS / name).convert_alpha()
    scale = size / max(img.get_size())
    return pygame.transform.smoothscale(img, (round(img.get_width() * scale), round(img.get_height() * scale)))


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 'es' if word.endswith(('sh', 'x')) else 's'}"


def segments(n, x, y, w, h, gap):
    bw = (w - gap * (n - 1)) / n
    return [pygame.Rect(round(x + i * (bw + gap)), y, round(bw), h) for i in range(n)]


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def lerp(a, b, t):
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


class Motion:
    def __init__(self):
        self.shown = None
        self.agent_from = self.box_from = self.box_to = self.start = None

    def update(self, board, now):
        state = (board.agent, frozenset(board.boxes))
        if state == self.shown:
            return
        prev, self.shown, self.start = self.shown, state, None
        if prev is None or not adjacent(prev[0], board.agent):
            return
        gone, new = prev[1] - state[1], state[1] - prev[1]
        if len(gone) != len(new) or len(gone) > 1 or (gone and not adjacent(*gone, *new)):
            return
        self.agent_from, self.start = prev[0], now
        self.box_from, self.box_to = (next(iter(gone)), next(iter(new))) if gone else (None, None)

    def progress(self, now):
        if self.start is None or now - self.start >= theme.MOVE_MS:
            return 1.0
        return theme.ease_out((now - self.start) / theme.MOVE_MS)

    def landed(self, now):
        if self.start is None or self.box_to is None:
            return None
        t = (now - self.start - theme.MOVE_MS) / theme.PULSE_MS
        return t if 0 <= t < 1 else None


class Button:
    def __init__(self, label, rect, action, style="secondary", selected=None, enabled=None,
                 font="body_bold", radius=theme.RADIUS["button"]):
        self.label, self.rect, self.action, self.style = label, pygame.Rect(rect), action, style
        self.selected, self.enabled, self.font, self.radius = selected, enabled, font, radius

    def text(self):
        return self.label() if callable(self.label) else self.label

    def is_selected(self):
        return self.selected is not None and self.selected()

    def is_enabled(self):
        return self.enabled is None or self.enabled()


def run():
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    levels = sorted(LEVELS_DIR.glob("*.txt"))
    if not levels:
        raise SystemExit(f"no levels in {LEVELS_DIR}")
    App(levels).loop()
    pygame.quit()
    bridge.shutdown()


class App:
    def __init__(self, levels):
        theme.init()
        self.levels, self.idx, self.page = levels, 0, "menu"
        self.level_data = [parse(level.read_text()) for level in levels]
        self.floors = [floor(walls, agent) for walls, _, _, agent in self.level_data]
        self.mode, self.algo, self.heur, self.prune = "watch", "astar", "h_match", True
        self.plan, self.stats, self.fail, self.msg, self.status = [], None, None, "", "Ready"
        self.job = self.dead_job = None
        self.dead, self.dead_seen, self.hand_cursor = None, None, False
        self.build_sidebar()
        self.build_menu()
        self.open_menu()
        self.wall = load_sprite("wall.png", TILE)
        self.crate = load_sprite("crate.png", TILE - 6)
        self.crate_on_goal = self.crate.copy()
        tint = theme.mix(COLOR["box_on_goal"], (255, 255, 255), 0.45)
        self.crate_on_goal.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        pygame.draw.rect(self.crate_on_goal, COLOR["box_on_goal"], self.crate_on_goal.get_rect(), 3, border_radius=4)
        self.player = load_sprite("player.png", TILE - 6)
        self.robot = load_sprite("AI-sprite.png", TILE - 6)
        self.previews = [self.make_preview(i) for i in range(len(levels))]

    def build_sidebar(self):
        x, w = PAD, SIDE - 2 * PAD
        self.labels, self.groups, self.buttons = [], [], []
        idle = lambda: self.job is None
        y = STATS_BOX.bottom + GAP - 4

        def segmented(options, gx, gw, current, action, enabled=idle):
            track = pygame.Rect(gx, y, gw, SEG_H)
            self.groups.append(track)
            for (label, value), r in zip(options, segments(len(options), gx + 3, y + 3, gw - 6, SEG_H - 6, gap=2)):
                self.buttons.append(Button(label, r, lambda v=value: action(v), style="segment", font="small_bold",
                                           selected=lambda v=value: current() == v, enabled=enabled,
                                           radius=theme.RADIUS["segment"] - 2))

        self.labels.append(("Algorithm", (x, y)))
        y += 20
        segmented([(label, algo) for algo, label in ALGOS.items()], x, w,
                  lambda: self.algo, lambda v: self.pick(algo=v))
        y += SEG_H + GAP - 8

        hw = (w - 12) * 3 // 5
        self.labels += [("Heuristic", (x, y)), ("Pruning", (x + hw + 12, y))]
        y += 20
        uses_heur = lambda: self.algo in USES_HEUR
        segmented([(h, h) for h in HEURS], x, hw, lambda: self.heur if uses_heur() else None,
                  lambda v: self.pick(heur=v), enabled=lambda: idle() and uses_heur())
        segmented([("On", True), ("Off", False)], x + hw + 12, w - hw - 12, lambda: self.prune,
                  lambda v: self.pick(prune=v))
        y += SEG_H + GAP

        versus = lambda: self.mode == "versus"
        self.buttons += [
            Button(lambda: "Undo" if versus() else "Solve", (x, y, w, BTN_H),
                   lambda: self.undo() if versus() else self.solve(), style="primary", enabled=idle),
            Button(lambda: "Restart" if versus() else "Reset", (x, y + BTN_H + 10, w, BTN_H), self.reset, enabled=idle),
            Button("Quit to levels", (x, y + 2 * (BTN_H + 10), w, BTN_H), self.open_menu, style="ghost"),
        ]
        self.side_h = y + 3 * BTN_H + 2 * 10 + PAD

    def build_alert(self):
        self.alert_rect = pygame.Rect((0, 0), ALERT)
        self.alert_rect.center = self.screen.get_rect().center
        r, gap = self.alert_rect, 10
        bw = (r.w - 2 * PAD - 2 * gap) // 3
        y = r.bottom - PAD - BTN_H
        self.alert_buttons = [Button(label, (r.x + PAD + i * (bw + gap), y, bw, BTN_H), action, style)
                              for i, (label, action, style) in enumerate([("Dismiss", self.dismiss_alert, "ghost"),
                                                                          ("Restart", self.reset, "secondary"),
                                                                          ("Undo", self.undo, "primary")])]

    def build_menu(self):
        arrow_y = INSET.centery - ARROW // 2
        self.prev_btn = Button("", (CARD.x - 28 - ARROW, arrow_y, ARROW, ARROW), lambda: self.select(-1),
                               enabled=lambda: self.idx > 0, radius=ARROW // 2)
        self.next_btn = Button("", (CARD.right + 28, arrow_y, ARROW, ARROW), lambda: self.select(1),
                               enabled=lambda: self.idx < len(self.levels) - 1, radius=ARROW // 2)
        bw, gap, bh, by = 220, 16, BTN_H + 6, CARD.bottom + 56
        bx = (MENU_W - 2 * bw - gap) // 2
        self.menu_buttons = [
            self.prev_btn, self.next_btn,
            Button("Watch AI", (bx, by, bw, bh), lambda: self.start("watch"), style="primary"),
            Button("Player vs AI", (bx + bw + gap, by, bw, bh), lambda: self.start("versus"), style="primary"),
        ]
        self.menu_size = (MENU_W, by + bh + 44)

    def make_preview(self, i):
        walls, _, boxes, agent = self.level_data[i]
        surf = pygame.Surface(((max(x for x, _ in walls) + 1) * TILE, (max(y for _, y in walls) + 1) * TILE))
        surf.fill(COLOR["bg"])
        self.draw_board(surf, 0, 0, i, Board(boxes, agent))
        box = INSET.inflate(-40, -40)
        scale = min(box.w / surf.get_width(), box.h / surf.get_height(), 1)
        return pygame.transform.smoothscale(surf, (round(surf.get_width() * scale), round(surf.get_height() * scale)))

    def open_menu(self):
        self.page, self.job = "menu", None
        pygame.time.set_timer(STEP, 0)
        self.screen = pygame.display.set_mode(self.menu_size)
        pygame.display.set_caption("Sokoban — choose a level")

    def select(self, d):
        self.idx = min(max(self.idx + d, 0), len(self.levels) - 1)

    def start(self, mode):
        self.page, self.mode = "game", mode
        self.load()

    @property
    def level(self):
        return self.levels[self.idx]

    def board_px(self):
        walls = self.level_data[self.idx][0]
        return (max(x for x, _ in walls) + 1) * TILE, (max(y for _, y in walls) + 1) * TILE

    def load(self):
        bw, bh = self.board_px()
        content_w = 2 * bw + GAP if self.mode == "versus" else max(bw, WATCH_MIN_W)
        size = (SIDE + 2 * GAP + content_w, max(GAP + HEADER_H + bh + FOOTER_H[self.mode], self.side_h))
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption(f"Sokoban — {self.level.name}")
        self.build_alert()
        if self.mode == "versus":
            self.new_game()
        else:
            self.reset()

    def reset(self):
        self.walls, self.goals, boxes, agent = self.level_data[self.idx]
        self.you, self.ai = Board(boxes, agent), Board(boxes, agent)
        self.motion = {id(self.you): Motion(), id(self.ai): Motion()}
        self.history, self.finished, self.msg, self.job = [], False, "", None
        pygame.time.set_timer(STEP, 0)
        if self.mode == "versus":
            self.check_deadlock()
            self.status = self.versus_status()
        else:
            self.plan, self.stats, self.fail, self.status = [], None, None, "Ready"

    def pick(self, **setting):
        if all(getattr(self, k) == v for k, v in setting.items()):
            return
        for k, v in setting.items():
            setattr(self, k, v)
        if self.mode == "versus":
            self.new_game()
        else:
            self.reset()

    def setup_label(self):
        parts = [ALGOS[self.algo]] + ([self.heur] if self.algo in USES_HEUR else [])
        return " · ".join(parts + [f"pruning {'on' if self.prune else 'off'}"])

    def think(self, busy, then):
        self.plan, self.stats, self.fail, self.status = [], None, None, busy
        self.job = (bridge.submit(bridge.solve, self.level, self.algo, self.heur, self.prune), then)

    def poll_jobs(self):
        if self.job and self.job[0].done():
            future, then = self.job
            self.job = None
            try:
                plan, self.stats = future.result()
            except Exception as ex:
                self.fail, self.msg = "Error", f"Engine error: {ex}"
            else:
                cost = self.stats and self.stats["cost"]
                if plan is None or not isinstance(cost, int):
                    self.fail = GAVE_UP.get(str(cost), "No solution")
                else:
                    self.plan = plan
            then()
        if self.dead_job and self.dead_job[0].done():
            future, boxes = self.dead_job
            self.dead_job = None
            if boxes == self.you.boxes:
                self.dead = None if future.exception() else future.result()
                if not self.dead:
                    self.dead_seen = None

    def ai_step(self):
        if self.ai.moves >= len(self.plan):
            return False
        try:
            self.ai.move(self.walls, self.plan[self.ai.moves])
        except ValueError as ex:
            self.plan, self.fail, self.msg = [], "Error", str(ex)
            return False
        return True

    def play_step(self):
        if self.ai_step():
            return
        pygame.time.set_timer(STEP, 0)
        if self.mode == "versus":
            self.finished = True
            self.status = self.versus_status()
        elif self.status == "Playing":
            self.status = self.fail or ("Solved!" if self.ai.boxes <= self.goals else "Done")

    def solve(self):
        self.reset()
        self.think("Solving...", self.start_replay)

    def start_replay(self):
        if self.fail:
            self.status = self.fail
        else:
            self.status = "Playing"
            pygame.time.set_timer(STEP, REPLAY_MS["watch"])

    def new_game(self):
        self.reset()
        self.think("AI thinking...", lambda: setattr(self, "status", self.versus_status()))

    def player_move(self, m):
        if self.job or self.finished or self.you.boxes == self.goals or self.alert_open():
            return
        before = (self.you.snapshot(), self.ai.snapshot())
        try:
            self.you.move(self.walls, m)
        except ValueError:
            return
        self.history.append(before)
        self.ai_step()
        self.check_deadlock()
        if self.you.boxes == self.goals:
            pygame.time.set_timer(STEP, REPLAY_MS["versus"])
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

    def alert_open(self):
        return (self.page == "game" and self.mode == "versus" and bool(self.dead)
                and frozenset(self.dead) != self.dead_seen
                and self.motion[id(self.you)].progress(pygame.time.get_ticks()) == 1)

    def dismiss_alert(self):
        self.dead_seen = frozenset(self.dead)

    def check_deadlock(self):
        self.dead_job = (bridge.submit(bridge.dead_boxes, self.level, self.you.boxes), self.you.boxes)

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
        if not self.finished:
            return None
        ai_solved = self.ai.boxes == self.goals

        def win(you, ai):
            if not ai_solved or you < ai:
                return "You"
            return "AI" if ai < you else "Tie"

        return win(self.you.moves, self.ai.moves), win(self.you.pushes, self.ai.pushes)

    def current_buttons(self):
        if self.page == "menu":
            return self.menu_buttons
        return self.alert_buttons if self.alert_open() else self.buttons

    def loop(self):
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN:
                    if self.page == "game" and self.mode == "versus" and e.key in MOVE_KEYS:
                        self.player_move(MOVE_KEYS[e.key])
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.click(e.pos)
                elif e.type == STEP and self.page == "game":
                    self.play_step()
            self.poll_jobs()
            self.update_cursor()
            self.draw()
            clock.tick(60)

    def click(self, pos):
        for b in self.current_buttons():
            if b.rect.collidepoint(pos) and b.is_enabled():
                b.action()
                return

    def update_cursor(self):
        pos = pygame.mouse.get_pos()
        hand = any(b.rect.collidepoint(pos) and b.is_enabled() for b in self.current_buttons())
        if hand != self.hand_cursor:
            self.hand_cursor = hand
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass

    def text(self, s, font, color, pos, anchor="topleft"):
        return theme.text(self.screen, s, font, color, pos, anchor)

    def level_name(self, i):
        return self.levels[i].stem.split("_", 1)[-1].replace("_", " ").capitalize()

    def draw_buttons(self, buttons):
        mouse = pygame.mouse.get_pos()
        for b in buttons:
            style = "selected" if b.style == "segment" and b.is_selected() else b.style
            theme.button(self.screen, b.rect, b.text(), style, b.rect.collidepoint(mouse), b.is_enabled(),
                         b.font, b.radius)

    def draw_board(self, surf, ox, oy, i, board, dead=(), sprite=None, motion=None):
        walls, goals, _, _ = self.level_data[i]
        now = pygame.time.get_ticks()
        if motion:
            motion.update(board, now)
        t = motion.progress(now) if motion else 1.0

        def cell_rect(cell):
            return pygame.Rect(round(ox + cell[0] * TILE), round(oy + cell[1] * TILE), TILE, TILE)

        for cell in self.floors[i]:
            pygame.draw.rect(surf, COLOR["floor" if sum(cell) % 2 else "floor_alt"], cell_rect(cell))
        for cell in walls:
            surf.blit(self.wall, self.wall.get_rect(center=cell_rect(cell).center))
        for cell in goals:
            c = cell_rect(cell).center
            pygame.draw.circle(surf, COLOR["goal"], c, TILE // 4, 3)
            pygame.draw.circle(surf, COLOR["goal"], c, 4)
        sliding = t < 1
        for cell in board.boxes:
            at = cell
            if sliding and cell == motion.box_to:
                at = lerp(motion.box_from, cell, t)
                cell = motion.box_from
            img = self.crate_on_goal if cell in goals else self.crate
            r = img.get_rect(center=cell_rect(at).center)
            surf.blit(img, r)
            if cell in dead:
                pygame.draw.rect(surf, COLOR["danger"], r.inflate(4, 4), 3, border_radius=5)
        pulse = motion.landed(now) if motion else None
        if pulse is not None and motion.box_to in goals and motion.box_to in board.boxes:
            theme.ring(surf, cell_rect(motion.box_to).center, pulse)
        sprite = sprite or self.player
        at = lerp(motion.agent_from, board.agent, t) if sliding else board.agent
        hop = round(theme.HOP * math.sin(math.pi * t)) if sliding else 0
        surf.blit(sprite, sprite.get_rect(center=cell_rect(at).center).move(0, -hop))

    def draw_stage(self, ox, oy, board, dead=(), thinking=False, sprite=None):
        rect = pygame.Rect((ox, oy), self.board_px())
        theme.shadow(self.screen, rect, 6, offset=6, spread=4)
        self.draw_board(self.screen, ox, oy, self.idx, board, dead, sprite, self.motion[id(board)])
        if thinking:
            veil = pygame.Surface(rect.size, pygame.SRCALPHA)
            veil.fill((*COLOR["bg"], 200))
            self.screen.blit(veil, rect)
            theme.spinner(self.screen, (rect.centerx, rect.centery - 14), pygame.time.get_ticks())
            self.text("Thinking…", "body", "muted", (rect.centerx, rect.centery + 12), "midtop")

    def draw_header(self, ox, who, board, right):
        r = self.text(who, "h1", "text", (ox, GAP - 4))
        self.text(f"{plural(board.moves, 'move')} · {plural(board.pushes, 'push')}", "body", "muted",
                  (r.right + 12, r.bottom - 3), "bottomleft")
        if who == "AI" and self.plan and board.moves >= len(self.plan) and not self.finished:
            theme.pill(self.screen, "Done, waiting", "muted", (right, GAP - 2))

    def stat_rows(self):
        s, ai = self.stats or {}, self.ai
        solved = isinstance(s.get("cost"), int)
        dash = "–"
        return [
            ("Boxes on goal", f"{len(ai.boxes & self.goals)} / {len(ai.boxes)}"),
            ("Moves used", f"{ai.moves} / {len(self.plan)}" if solved else str(ai.moves)),
            ("Box pushes", f"{ai.pushes} / {s['cost']}" if solved else str(ai.pushes)),
            ("Pushes left", str(s["cost"] - ai.pushes) if solved else dash),
            ("States checked", f"{s['nodes']:,}" if s else dash),
            ("Most waiting", f"{s['max_frontier']:,}" if s else dash),
            ("Think time", f"{s['time_ms']:,} ms" if s else dash),
        ]

    def versus_rows(self):
        s, you, ai = self.stats or {}, self.you, self.ai
        on_goal = lambda b: f"{len(b.boxes & self.goals)} / {len(b.boxes)}"
        win = self.winners()
        dash = "–"
        return [
            ("", "YOU", "AI"),
            ("Moves", str(you.moves), str(ai.moves)),
            ("Pushes", str(you.pushes), str(ai.pushes)),
            ("Boxes on goal", on_goal(you), on_goal(ai)),
            ("AI plan", f"{len(self.plan)} moves, {s['cost']} pushes" if self.plan else dash),
            ("Fewest moves", win[0] if win else dash),
            ("Fewest pushes", win[1] if win else dash),
        ]

    def draw_sidebar(self):
        h = self.screen.get_height()
        pygame.draw.rect(self.screen, COLOR["surface"], (0, 0, SIDE, h))
        pygame.draw.line(self.screen, COLOR["border"], (SIDE - 1, 0), (SIDE - 1, h))

        box = STATS_BOX
        theme.panel(self.screen, box, drop=False)
        x, rx, y = box.x + PAD, box.right - PAD, box.y + PAD
        r = self.text(f"Level {self.idx + 1}", "h1", "text", (x, y - 2))
        self.text(f"of {len(self.levels)}", "body", "faint", (r.right + 8, r.bottom - 4), "bottomleft")
        failed = self.status.startswith(("AI: ", "Error", "Gave up", "No solution"))
        theme.pill(self.screen, self.status, STATUS_COLOR.get(self.status, "danger" if failed else "muted"), (rx, y))
        self.text(self.level_name(self.idx), "body", "muted", (x, y + 32))
        self.text(self.setup_label(), "small_bold", "accent", (x, y + 58))
        pygame.draw.line(self.screen, COLOR["border"], (x, y + STATS_TOP - 14), (rx, y + STATS_TOP - 14))
        y += STATS_TOP - 4
        versus = self.mode == "versus"
        for i, (label, *values) in enumerate(self.versus_rows() if versus else self.stat_rows()):
            header = versus and i == 0
            font, color, dy = ("label", "faint", 4) if header else ("body_bold", "text", 0)
            self.text(label, "body", "muted", (x, y))
            if len(values) == 2:
                self.text(values[0], font, color, (rx - 76, y + dy), "topright")
            self.text(values[-1], font, color, (rx, y + dy), "topright")
            y += ROW

        for label, pos in self.labels:
            theme.label(self.screen, label, pos)
        for track in self.groups:
            pygame.draw.rect(self.screen, COLOR["bg"], track, border_radius=theme.RADIUS["segment"])
        self.draw_buttons(self.buttons)

    def draw_footer_versus(self, left, y, width):
        win = self.winners()
        if win:
            card = pygame.Rect(left, y, width, 66)
            theme.panel(self.screen, card)
            half = width // 2
            for i, (title, winner, you, ai) in enumerate([("Fewest moves", win[0], self.you.moves, self.ai.moves),
                                                          ("Fewest pushes", win[1], self.you.pushes, self.ai.pushes)]):
                hx = left + i * half
                theme.label(self.screen, title, (hx + PAD + 4, y + 13))
                verdict = {"You": "You win", "AI": "AI wins", "Tie": "Tie"}[winner]
                self.text(verdict, "h2", WINNER_COLOR[winner], (hx + PAD + 4, y + 31))
                self.text(f"You {you}  ·  AI {ai}", "body", "muted", (hx + half - PAD - 4, y + 35), "topright")
            pygame.draw.line(self.screen, COLOR["border"], (left + half, y + 12), (left + half, y + 54))
            y += 66 + 14
        else:
            self.text(self.msg or "Use the arrow keys to move", "body", "danger" if self.msg else "muted", (left, y))
            y += 34

    def draw_alert(self):
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((*COLOR["bg"], 170))
        self.screen.blit(veil, (0, 0))
        r = self.alert_rect
        theme.panel(self.screen, r)
        pygame.draw.rect(self.screen, COLOR["danger"], (r.x, r.y, r.w, 4),
                         border_top_left_radius=theme.RADIUS["panel"], border_top_right_radius=theme.RADIUS["panel"])
        icon = (r.x + PAD + 20, r.y + PAD + 28)
        pygame.draw.circle(self.screen, theme.mix(COLOR["panel"], COLOR["danger"], 0.22), icon, 20)
        self.text("!", "h1", "danger", icon, "center")
        tx = icon[0] + 34
        self.text("Deadlock", "h1", "text", (tx, r.y + PAD + 12))
        n = len(self.dead)
        self.text(f"{plural(n, 'box')} can never reach a goal,", "body", "muted", (tx, r.y + PAD + 52))
        self.text("so this level can't be solved from here.", "body", "muted", (tx, r.y + PAD + 76))
        self.draw_buttons(self.alert_buttons)

    def draw_game(self):
        bw, bh = self.board_px()
        top = GAP + HEADER_H
        thinking = self.job is not None
        if self.mode == "versus":
            left, right = SIDE + GAP, SIDE + 2 * GAP + bw
            self.draw_header(left, "You", self.you, left + bw)
            self.draw_header(right, "AI", self.ai, right + bw)
            self.draw_stage(left, top, self.you, self.dead or ())
            self.draw_stage(right, top, self.ai, thinking=thinking, sprite=self.robot)
            self.draw_footer_versus(left, top + bh + 24, 2 * bw + GAP)
        else:
            content_w = self.screen.get_width() - SIDE - 2 * GAP
            left = SIDE + GAP + (content_w - bw) // 2
            self.draw_header(left, "AI", self.ai, left + bw)
            self.draw_stage(left, top, self.ai, thinking=thinking, sprite=self.robot)
            if self.msg:
                self.text(self.msg, "body", "danger", (left, top + bh + 24))
        self.draw_sidebar()

    def draw_menu(self):
        mid = MENU_W // 2
        self.text("Sokoban", "title", "text", (mid, 36), "midtop")
        self.text("Choose a level, then how to play", "body", "muted", (mid, 94), "midtop")

        theme.panel(self.screen, CARD)
        pygame.draw.rect(self.screen, COLOR["bg"], INSET, border_radius=theme.RADIUS["panel"] - 4)
        preview = self.previews[self.idx]
        self.screen.blit(preview, preview.get_rect(center=INSET.center))
        r = self.text(f"LEVEL {self.idx + 1} OF {len(self.levels)}", "label", "faint",
                      (mid, INSET.bottom + 20), "midtop")
        r = self.text(self.level_name(self.idx), "h1", "text", (mid, r.bottom + 6), "midtop")
        boxes = len(self.level_data[self.idx][2])
        theme.pill(self.screen, plural(boxes, "box"), "accent", (mid, r.bottom + 10), "midtop")

        n, step_x = len(self.levels), 18
        for i in range(n):
            c = (mid - (n - 1) * step_x // 2 + i * step_x, CARD.bottom + 26)
            on = i == self.idx
            pygame.draw.circle(self.screen, COLOR["accent" if on else "raised"], c, 5 if on else 4)

        self.draw_buttons(self.menu_buttons)
        for b, d in [(self.prev_btn, -1), (self.next_btn, 1)]:
            cx, cy = b.rect.center
            pts = [(cx + 8 * d, cy), (cx - 5 * d, cy - 11), (cx - 5 * d, cy + 11)]
            pygame.draw.polygon(self.screen, COLOR["text" if b.is_enabled() else "faint"], pts)

    def draw(self):
        self.screen.fill(COLOR["bg"])
        if self.page == "menu":
            self.draw_menu()
        else:
            self.draw_game()
            if self.alert_open():
                self.draw_alert()
        pygame.display.flip()
