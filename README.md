# Autonomous Sokoban Solver

SWI-Prolog engine (all search/reasoning) + Pygame GUI via PySwip. See `sokoban-project-plan.md`.

## Setup
1. Install SWI-Prolog (64-bit) and make sure `swipl` is on PATH (PySwip needs it).
2. `uv sync`

## Run
- GUI: `uv run sokoban-solver` (Left/Right = level, Space = solve, R = reset)
- Tests: `uv run pytest` and `swipl -g run_tests -t halt tests/test_state.pl`

## Layout
- `prolog/` engine: `solver.pl` exposes `solve(LevelFile, Algo, Heur, Prune, Plan, Stats)`
- `levels/` level files (`#` wall, `.` goal, `$` box, `*` box on goal, `@` agent, `+` agent on goal)
- `src/sokoban_solver/` GUI (`gui.py`), PySwip bridge (`bridge.py`), level parsing (`level.py`)
