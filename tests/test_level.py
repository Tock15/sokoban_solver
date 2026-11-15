from sokoban_solver.level import LEVELS_DIR, parse, step


def test_tiny_level_fake_plan_solves():
    walls, goals, boxes, agent = parse((LEVELS_DIR / "01_tiny.txt").read_text())
    for m in ["r", "r"]:
        boxes, agent = step(walls, boxes, agent, m)
    assert boxes == goals


def test_push_into_wall_is_illegal():
    walls, goals, boxes, agent = parse("#####\n#@$#\n#####")
    try:
        step(walls, boxes, agent, "r")
    except ValueError:
        return
    raise AssertionError("expected illegal move")
