"""PySwip bridge to the Prolog engine: solve/6 and dead_boxes/3 in prolog/solver.pl."""
from .level import ROOT

_prolog = None


def _engine():
    global _prolog
    if _prolog is None:
        from pyswip import Prolog  # imported lazily: needs SWI-Prolog installed

        _prolog = Prolog()
        _prolog.consult((ROOT / "prolog" / "solver.pl").as_posix())
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


def dead_boxes(level_file, boxes):
    """Return the boxes (as (x, y)) that can never reach a goal. Call after each push."""
    q = f"dead_boxes('{_path(level_file)}', {[list(b) for b in boxes]}, D)"
    res = list(_engine().query(q, maxresult=1))
    return [tuple(b) for b in res[0]["D"]] if res else []
