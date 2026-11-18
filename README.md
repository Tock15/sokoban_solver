# Autonomous Sokoban Solver

SWI-Prolog engine (all search/reasoning) + Pygame GUI via PySwip. See `sokoban-project-plan.md`.

## Setup
1. Install SWI-Prolog (64-bit) and make sure `swipl` is on PATH (PySwip needs it).
2. `uv sync`

## Run
- GUI: `uv run sokoban-solver`. Everything is buttons; the only keys are the arrows that move you in Player vs AI.
  It opens on the level selector at level 1: the arrow buttons change level, then pick Watch AI or Player vs AI.
  On the game page, pick algorithm / heuristic / pruning in the sidebar; Quit goes back to the level selector.
  - Watch AI: Solve, Reset
  - Player vs AI: arrow keys = move (the AI moves once per legal move of yours), Undo, Restart (both boards)
- Tests: `uv run pytest` and `swipl -g run_tests -t halt tests/test_state.pl tests/test_engine.pl`

## Layout
- `prolog/` engine: `solver.pl` exposes `solve(LevelFile, Algo, Heur, Prune, Plan, Stats)`
- `levels/` level files (`#` wall, `.` goal, `$` box, `*` box on goal, `@` agent, `+` agent on goal)
- `src/sokoban_solver/` GUI (`gui.py`), PySwip bridge (`bridge.py`), level parsing (`level.py`)
