import queue
import threading
from concurrent.futures import Future

from .level import ROOT

_prolog = None
_jobs = queue.Queue()


def _engine():
    global _prolog
    if _prolog is None:
        from pyswip import Prolog

        _prolog = Prolog()
        for f in ("solver.pl", "verify.pl"):
            _prolog.consult((ROOT / "prolog" / f).as_posix())
    return _prolog


def _worker():
    while True:
        fn, args, future = _jobs.get()
        try:
            future.set_result(fn(*args))
        except Exception as ex:
            future.set_exception(ex)


threading.Thread(target=_worker, name="prolog", daemon=True).start()


def submit(fn, *args):
    future = Future()
    try:
        _engine()
    except Exception as ex:
        future.set_exception(ex)
        return future
    _jobs.put((fn, args, future))
    return future


def shutdown(timeout=1.0):
    if _prolog is None:
        return

    def release():
        from pyswip.core import _lib

        _lib.PL_thread_destroy_engine()

    try:
        submit(release).result(timeout)
    except TimeoutError:
        pass
def _path(level_file):
    return level_file.as_posix().replace("'", "\\'")


def solve(level_file, algo="astar", heur="h_sum", prune=True):
    path = level_file.as_posix().replace("\\", "\\\\").replace("'", "\\'")
    q = f"solve('{path}', {algo}, {heur}, {str(prune).lower()}, Plan, stats(N, T, C, F))"
    res = list(_engine().query(q, maxresult=1))
    if not res:
        return None, None
    r = res[0]
    stats = {"nodes": r["N"], "time_ms": r["T"], "cost": r["C"], "max_frontier": r["F"]}
    return [str(m) for m in r["Plan"]], stats


def verify(level_file, heur, prune):
    q = f"verify('{_path(level_file)}', {heur}, {str(prune).lower()}, report(H, C, A, V))"
    res = list(_engine().query(q, maxresult=1))
    if not res:
        return None
    r = res[0]
    return {"h_start": r["H"], "c_star": r["C"], "admissible": str(r["A"]) == "true", "violations": r["V"]}


def set_limits(nodes, seconds):
    list(_engine().query(f"retractall(solver:limit(_, _)), assertz(solver:limit(nodes, {int(nodes)})), "
                         f"assertz(solver:limit(seconds, {int(seconds)}))"))


def dead_boxes(level_file, boxes):
    q = f"dead_boxes('{_path(level_file)}', {[list(b) for b in boxes]}, D)"
    res = list(_engine().query(q, maxresult=1))
    return [tuple(b) for b in res[0]["D"]] if res else []
