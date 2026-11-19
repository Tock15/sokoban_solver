import pytest

from sokoban_solver import bridge
from sokoban_solver.experiments import b_star
from sokoban_solver.level import LEVELS_DIR


@pytest.mark.parametrize("nodes, depth, b", [(6, 2, 2.0), (14, 3, 2.0), (39, 3, 3.0), (2, 2, 1.0)])
def test_b_star_inverts_tree_size(nodes, depth, b):
    # a uniform tree with branching b and depth d has 1 + b + ... + b^d = N + 1 nodes
    assert b_star(nodes, depth) == pytest.approx(b, abs=1e-3)


def test_b_star_undefined_without_depth():
    assert b_star(5, 0) is None


def test_verify_reports_admissible_and_consistent():
    v = bridge.verify(LEVELS_DIR / "02_two_boxes.txt", "h_match", True)
    assert v["admissible"] and v["violations"] == 0 and v["h_start"] <= v["c_star"] == 4
