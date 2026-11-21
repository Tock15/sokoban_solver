import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from sokoban_solver import bridge, gui, theme  # noqa: E402
from sokoban_solver.level import LEVELS_DIR, Board  # noqa: E402

WALLS = {(x, y) for x in range(8) for y in (0, 2)}


@pytest.fixture
def app():
    pygame.init()
    yield gui.App(sorted(LEVELS_DIR.glob("*.txt")))
    pygame.quit()


def settle(app, timeout=30):
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
    assert app.status == "Solving..." and not app.buttons[-3].is_enabled()
    app.draw()
    settle(app)
    while app.status == "Playing":
        app.play_step()
    assert app.status == "Solved!" and app.ai.boxes == app.goals


def test_versus_moves_undo_and_result(app):
    app.idx = 1
    app.start("versus")
    settle(app)
    app.player_move("l")
    assert (app.you.moves, app.ai.moves) == (0, 0)
    app.player_move(app.plan[0])
    assert (app.you.moves, app.ai.moves) == (1, 1)
    app.undo()
    assert (app.you.moves, app.ai.moves, app.history) == (0, 0, [])
    for m in app.plan:
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
    assert motion.progress(0) == 1
    board.move(WALLS, "r")
    motion.update(board, 1000)
    assert (motion.agent_from, motion.box_from, motion.box_to) == ((1, 1), (2, 1), (3, 1))
    assert 0 < motion.progress(1000 + theme.MOVE_MS // 2) < 1
    assert motion.progress(1000 + theme.MOVE_MS) == 1
    assert motion.landed(1000 + theme.MOVE_MS + 1) is not None
    board.restore(({(5, 1)}, (2, 1), 0, 0))
    motion.update(board, 2000)
    assert motion.progress(2000) == 1


def test_deadlock_alert_blocks_moves_until_undo_or_dismiss(app):
    app.idx = 1
    app.start("versus")
    settle(app)
    app.player_move("r")
    app.player_move("u")
    settle(app)
    app.motion[id(app.you)].start = None
    assert app.dead == [(2, 1)] and app.alert_open()
    assert app.current_buttons() is app.alert_buttons
    app.draw()
    app.player_move("d")
    assert app.you.moves == 2
    app.click(app.alert_buttons[2].rect.center)
    settle(app)
    assert app.you.moves == 1 and not app.alert_open()
    app.player_move("u")
    settle(app)
    app.motion[id(app.you)].start = None
    app.click(app.alert_buttons[0].rect.center)
    assert not app.alert_open() and app.dead == [(2, 1)]
    app.player_move("d")
    assert app.you.moves == 3
