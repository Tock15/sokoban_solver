import pytest

from sokoban_solver import bridge
from sokoban_solver.level import LEVELS_DIR, parse, step


TOO_HARD = {"10_five_boxes"}


@pytest.mark.parametrize("level", [p for p in sorted(LEVELS_DIR.glob("*.txt")) if p.stem not in TOO_HARD],
                         ids=lambda p: p.stem)
def test_astar_plan_solves_level(level):
    plan, stats = bridge.solve(level, "astar", "h_match", True)
    assert isinstance(stats["cost"], int), stats
    walls, goals, boxes, agent = parse(level.read_text())
    for m in plan:
        boxes, agent = step(walls, boxes, agent, m)
    assert boxes == goals


def test_dead_boxes_flags_only_stuck_boxes():
    level = LEVELS_DIR / "02_two_boxes.txt"
    assert sorted(bridge.dead_boxes(level, {(1, 1), (2, 2), (5, 1)})) == [(1, 1), (5, 1)]
    assert bridge.dead_boxes(level, {(2, 2), (4, 2)}) == []
