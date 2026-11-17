"""End to end: Python -> PySwip -> solve/6 -> replay the plan. Needs SWI-Prolog installed."""
import pytest

from sokoban_solver import bridge
from sokoban_solver.level import LEVELS_DIR, parse, step


@pytest.mark.parametrize("level", sorted(LEVELS_DIR.glob("*.txt")), ids=lambda p: p.stem)
def test_astar_plan_solves_level(level):
    plan, stats = bridge.solve(level, "astar", "h_match", True)
    assert isinstance(stats["cost"], int), stats
    walls, goals, boxes, agent = parse(level.read_text())
    for m in plan:
        boxes, agent = step(walls, boxes, agent, m)
    assert boxes == goals
