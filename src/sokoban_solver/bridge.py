"""PySwip bridge to the Prolog engine: solve(LevelFile, Algo, Heur, Prune, Plan, Stats)."""
from .level import ROOT

_prolog = None


def solve(level_file, algo="astar", heur="h_sum", prune=True):
    """Return (plan, stats) with plan a list of 'u'/'d'/'l'/'r' and stats a dict."""
    global _prolog
    if _prolog is None:
        from pyswip import Prolog  # imported lazily: needs SWI-Prolog installed

        _prolog = Prolog()
        _prolog.consult((ROOT / "prolog" / "solver.pl").as_posix())
    path = level_file.as_posix().replace("'", "\'")
    q = f"solve('{path}', {algo}, {heur}, {str(prune).lower()}, Plan, stats(N, T, C, F))"
    res = list(_prolog.query(q, maxresult=1))
    if not res:
        return None, None
    r = res[0]
    stats = {"nodes": r["N"], "time_ms": r["T"], "cost": r["C"], "max_frontier": r["F"]}
    return [str(m) for m in r["Plan"]], stats
