from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS_DIR = ROOT / "levels"
DIRS = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}


def parse(text):
    walls, goals, boxes, agent = set(), set(), set(), None
    for y, line in enumerate(text.splitlines()):
        for x, c in enumerate(line):
            if c == "#":
                walls.add((x, y))
            if c in ".*+":
                goals.add((x, y))
            if c in "$*":
                boxes.add((x, y))
            if c in "@+":
                agent = (x, y)
    if agent is None:
        raise ValueError("level has no agent (@ or +)")
    return walls, goals, boxes, agent


def step(walls, boxes, agent, move):
    dx, dy = DIRS[move]
    nxt = (agent[0] + dx, agent[1] + dy)
    if nxt in walls:
        raise ValueError(f"illegal move {move}: wall")
    if nxt in boxes:
        beyond = (nxt[0] + dx, nxt[1] + dy)
        if beyond in walls or beyond in boxes:
            raise ValueError(f"illegal move {move}: box blocked")
        boxes = (boxes - {nxt}) | {beyond}
    return boxes, nxt


class Board:
    def __init__(self, boxes, agent):
        self.boxes, self.agent, self.moves, self.pushes = boxes, agent, 0, 0

    def snapshot(self):
        return self.boxes, self.agent, self.moves, self.pushes

    def restore(self, snap):
        self.boxes, self.agent, self.moves, self.pushes = snap

    def move(self, walls, m):
        boxes, self.agent = step(walls, self.boxes, self.agent, m)
        self.pushes += boxes != self.boxes
        self.boxes = boxes
        self.moves += 1


def floor(walls, agent):
    seen, todo = {agent}, [agent]
    while todo:
        x, y = todo.pop()
        for dx, dy in DIRS.values():
            n = (x + dx, y + dy)
            if n not in seen and n not in walls:
                seen.add(n)
                todo.append(n)
    return seen
