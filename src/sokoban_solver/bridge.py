"""PySwip bridge to the Prolog engine: solve/6 and dead_boxes/3 in prolog/solver.pl."""
from .level import ROOT

_prolog = None


def _engine():
    global _prolog
    if _prolog is None:
        from pyswip import Prolog  # imported lazily: needs SWI-Prolog installed

        _prolog = Prolog()
        for f in ("solver.pl", "verify.pl"):
            _prolog.consult((ROOT / "prolog" / f).as_posix())
    return _prolog


def _path(level_file):
    return level_file.as_posix().replace("'", "\\'")


def solve(level_file, algo="astar", heur="h_sum", prune=True):
    """Return (plan, stats) with plan a list of 'u'/'d'/'l'/'r' and stats a dict."""
    q = f"solve('{_path(level_file)}', {algo}, {heur}, {str(prune).lower()}, Plan, stats(N, T, C, F))"
    res = list(_engine().query(q, maxresult=1))
    if not res:
        return None, None
    r = res[0]
    stats = {"nodes": r["N"], "time_ms": r["T"], "cost": r["C"], "max_frontier": r["F"]}
    return [str(m) for m in r["Plan"]], stats


def verify(level_file, heur, prune):
    """Heuristic checks via verify/4: dict(h_start, c_star, admissible, violations), or None if UCS/A* gave up."""
    q = f"verify('{_path(level_file)}', {heur}, {str(prune).lower()}, report(H, C, A, V))"
    res = list(_engine().query(q, maxresult=1))
    if not res:
        return None
    r = res[0]
    return {"h_start": r["H"], "c_star": r["C"], "admissible": str(r["A"]) == "true", "violations": r["V"]}


def set_limits(nodes, seconds):
    """Change the engine's per-search limits (default 1,000,000 nodes, 60 s) for this process."""
    list(_engine().query(f"retractall(solver:limit(_, _)), assertz(solver:limit(nodes, {int(nodes)})), "
                         f"assertz(solver:limit(seconds, {int(seconds)}))"))


def dead_boxes(level_file, boxes):
    """Return the boxes (as (x, y)) that can never reach a goal. Call after each push."""
    q = f"dead_boxes('{_path(level_file)}', {[list(b) for b in boxes]}, D)"
    res = list(_engine().query(q, maxresult=1))
    return [tuple(b) for b in res[0]["D"]] if res else []
