"""Headless smoke test of the GUI flow (dummy video driver). Needs SWI-Prolog, like test_bridge."""
import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from sokoban_solver import bridge, gui, theme  # noqa: E402
from sokoban_solver.level import LEVELS_DIR, Board  # noqa: E402

WALLS = {(x, y) for x in range(8) for y in (0, 2)}  # an open corridor for Motion tests


@pytest.fixture
def app():
    pygame.init()
    yield gui.App(sorted(LEVELS_DIR.glob("*.txt")))
    pygame.quit()


def settle(app, timeout=30):
    """Let background engine calls finish, as the main loop would."""
    end = time.time() + timeout
    while app.job or app.dead_job:
        assert time.time() < end, "engine took too long"
        app.poll_jobs()
        time.sleep(0.01)


def test_level_selector_arrows(app):
    assert (app.page, app.idx) == ("menu", 0)
    assert not app.prev_btn.is_enabled()
    for _ in range(10):
        app.click(app.next_btn.rect.center)
    assert app.idx == len(app.levels) - 1 and not app.next_btn.is_enabled()
    app.draw()


def test_watch_ai_solves_and_replays(app):
    app.start("watch")
    app.solve()
    assert app.status == "Solving..." and not app.buttons[-3].is_enabled()  # controls wait for the engine
    app.draw()
    settle(app)
    while app.status == "Playing":
        app.play_step()
    assert app.status == "Solved!" and app.ai.boxes == app.goals


def test_versus_moves_undo_and_result(app):
    app.idx = 1
    app.start("versus")
    settle(app)
    app.player_move("l")  # into the wall: nothing counts, the AI waits too
    assert (app.you.moves, app.ai.moves) == (0, 0)
    app.player_move(app.plan[0])
    assert (app.you.moves, app.ai.moves) == (1, 1)
    app.undo()
    assert (app.you.moves, app.ai.moves, app.history) == (0, 0, [])
    for m in app.plan:  # copy the AI move for move: a tie on both counts
        app.player_move(m)
    while not app.finished:
        app.play_step()
    assert app.you.boxes == app.goals and app.winners() == ("Tie", "Tie")
    app.draw()


def teardown_module():
    bridge.shutdown()


def test_motion_slides_one_step_and_snaps_bigger_jumps():
    board = Board({(2, 1)}, (1, 1))
    motion = gui.Motion()
    motion.update(board, 0)
    assert motion.progress(0) == 1  # first sight: nothing to slide from
    board.move(WALLS, "r")  # a push: agent and crate both move one cell
    motion.update(board, 1000)
    assert (motion.agent_from, motion.box_from, motion.box_to) == ((1, 1), (2, 1), (3, 1))
    assert 0 < motion.progress(1000 + theme.MOVE_MS // 2) < 1
    assert motion.progress(1000 + theme.MOVE_MS) == 1
    assert motion.landed(1000 + theme.MOVE_MS + 1) is not None
    board.restore(({(5, 1)}, (2, 1), 0, 0))  # the crate jumped 2 cells (restart / new solve): no slide
    motion.update(board, 2000)
    assert motion.progress(2000) == 1
