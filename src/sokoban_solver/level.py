"""Level parsing and move replay for display only (no search logic here)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS_DIR = ROOT / "levels"
DIRS = {"u": (0, -1), "d": (0, 1), "l": (-1, 0), "r": (1, 0)}


def parse(text):
    """Return (walls, goals, boxes, agent) using the same format as prolog/level.pl."""
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
    """Apply one u/d/l/r move. Raises if the engine returned an illegal move."""
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
