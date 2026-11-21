import pytest

from sokoban_solver.level import LEVELS_DIR, Board, floor, parse, step


def test_tiny_level_fake_plan_solves():
    walls, goals, boxes, agent = parse((LEVELS_DIR / "01_tiny.txt").read_text())
    for m in ["r", "r"]:
        boxes, agent = step(walls, boxes, agent, m)
    assert boxes == goals


def test_push_into_wall_is_illegal():
    walls, goals, boxes, agent = parse("#####\n#@$#\n#####")
    with pytest.raises(ValueError):
        step(walls, boxes, agent, "r")


def test_board_counts_moves_and_pushes():
    walls, goals, boxes, agent = parse("######\n#@ $.#\n######")
    b = Board(boxes, agent)
    b.move(walls, "r")
    b.move(walls, "r")
    assert (b.moves, b.pushes, b.boxes) == (2, 1, goals)


def test_board_illegal_move_changes_nothing():
    walls, _, boxes, agent = parse("#####\n#@$#\n#####")
    b = Board(boxes, agent)
    before = b.snapshot()
    with pytest.raises(ValueError):
        b.move(walls, "r")
    assert b.snapshot() == before


def test_board_restore_undoes():
    walls, _, boxes, agent = parse("######\n#@ $.#\n######")
    b = Board(boxes, agent)
    snap = b.snapshot()
    b.move(walls, "r")
    b.restore(snap)
    assert b.snapshot() == snap


def test_floor_is_the_inside_of_the_level():
    walls, _, _, agent = parse("#####\n#@ .#\n#####")
    assert floor(walls, agent) == {(1, 1), (2, 1), (3, 1)}
