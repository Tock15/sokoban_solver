"""PySwip bridge to the Prolog engine: solve(LevelFile, Algo, Heur, Prune, Plan, Stats).

The GUI calls everything through submit(), which runs it on one background "prolog" thread: the
window keeps redrawing during long searches, and queries never run at the same time (level facts
asserted by one query can't clash with another). Call shutdown() before exiting."""
import queue
import threading
from concurrent.futures import Future

from .level import ROOT

_prolog = None
_jobs = queue.Queue()


def _engine():
    """Start SWI-Prolog and load the engine once. Call it first from the main thread (submit() does):
    the background thread then gets its own secondary engine, which shutdown() can release cleanly."""
    global _prolog
    if _prolog is None:
        from pyswip import Prolog  # imported lazily: needs SWI-Prolog installed

        _prolog = Prolog()
        _prolog.consult((ROOT / "prolog" / "solver.pl").as_posix())
    return _prolog


def _worker():
    while True:
        fn, args, future = _jobs.get()
        try:
            future.set_result(fn(*args))
        except Exception as ex:  # handed to whoever reads the future
            future.set_exception(ex)


# daemon: closing the window never waits for a search that is still running
threading.Thread(target=_worker, name="prolog", daemon=True).start()


def submit(fn, *args):
    """Run fn(*args) on the Prolog thread, in order. Returns a concurrent.futures.Future."""
    future = Future()
    try:
        _engine()
    except Exception as ex:  # e.g. SWI-Prolog not installed: report it through the future
        future.set_exception(ex)
        return future
    _jobs.put((fn, args, future))
    return future


def shutdown(timeout=1.0):
    """Release the Prolog thread's engine so SWI-Prolog exits quietly. Skipped if a search is still running."""
    if _prolog is None:
        return

    def release():
        from pyswip.core import _lib

        _lib.PL_thread_destroy_engine()

    try:
        submit(release).result(timeout)
    except TimeoutError:
        pass


def solve(level_file, algo="astar", heur="h_sum", prune=True):
    """Return (plan, stats) with plan a list of 'u'/'d'/'l'/'r' and stats a dict."""
    path = level_file.as_posix().replace("\\", "\\\\").replace("'", "\\'")  # escape for a quoted Prolog atom
    q = f"solve('{path}', {algo}, {heur}, {str(prune).lower()}, Plan, stats(N, T, C, F))"
    res = list(_engine().query(q, maxresult=1))
    if not res:
        return None, None
    r = res[0]
    stats = {"nodes": r["N"], "time_ms": r["T"], "cost": r["C"], "max_frontier": r["F"]}
    return [str(m) for m in r["Plan"]], stats


def dead_boxes(level_file, boxes):
    """Boxes (set of (x, y)) that can never reach a goal, for the deadlock warning in Player vs AI mode.
    Returns None while the check isn't wired up; the GUI then shows 'not connected yet'.
    TODO: replace with the Prolog deadlock query and return the set of dead boxes."""
    return None
