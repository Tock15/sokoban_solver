import csv

from . import bridge
from .level import LEVELS_DIR, ROOT, parse

OUT = ROOT / "results" / "node_limit_30k"
NODE_LIMIT, TIME_LIMIT = 30_000, 600
SETUPS = [("bfs", "none"), ("ids", "none"), ("ucs", "none"), ("greedy", "h_sum"),
          ("greedy", "h_match"), ("astar", "h_sum"), ("astar", "h_match")]


def setup_name(algo, heur):
    return algo.upper() if heur == "none" else f"{algo.upper()} {heur}"


def b_star(nodes, depth):
    if depth < 1 or nodes < 1:
        return None
    total = lambda b: sum(b ** i for i in range(depth + 1))
    lo, hi = 0.0, float(nodes)
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if total(mid) < nodes + 1 else (lo, mid)
    return round(lo, 3)


def run_all(levels):
    rows = []
    for level in levels:
        boxes = len(parse(level.read_text())[2])
        for prune in (True, False):
            for algo, heur in SETUPS:
                _, s = bridge.solve(level, algo, heur, prune)
                s = s or {"nodes": "", "time_ms": "", "cost": "no_solution", "max_frontier": ""}
                solved = isinstance(s["cost"], int)
                rows.append({"level": level.stem, "boxes": boxes, "algo": algo, "heur": heur, "prune": prune,
                             "status": "solved" if solved else str(s["cost"]),
                             "cost": s["cost"] if solved else "", "optimal": "",
                             "nodes": s["nodes"], "max_frontier": s["max_frontier"], "time_ms": s["time_ms"],
                             "b_star": b_star(s["nodes"], s["cost"]) if solved else ""})
                print(level.stem, setup_name(algo, heur), "prune" if prune else "no-prune", rows[-1]["status"],
                      s["nodes"], "nodes", flush=True)
    ucs = {(r["level"], r["prune"]): r["cost"] for r in rows if r["algo"] == "ucs"}
    for r in rows:
        best = ucs[(r["level"], r["prune"])]
        if r["cost"] != "" and best != "":
            r["optimal"] = r["cost"] == best
    return rows


def verify_all(levels, rows):
    ucs_solved = {(r["level"], r["prune"]) for r in rows if r["algo"] == "ucs" and r["status"] == "solved"}
    out = []
    for level in levels:
        for heur in ("h_sum", "h_match"):
            for prune in (True, False):
                if (level.stem, prune) not in ucs_solved:
                    continue
                v = bridge.verify(level, heur, prune)
                if v:
                    out.append({"level": level.stem, "heur": heur, "prune": prune, **v})
    return out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def pivot(rows, prune, cell):
    names = [setup_name(a, h) for a, h in SETUPS]
    lines = ["| Level | Boxes | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for level in dict.fromkeys(r["level"] for r in rows):
        rs = {(r["algo"], r["heur"]): r for r in rows if r["level"] == level and r["prune"] == prune}
        first = next(iter(rs.values()))
        lines.append(f"| {level} | {first['boxes']} | " + " | ".join(cell(rs[s]) for s in SETUPS) + " |")
    return "\n".join(lines)


def tables(rows, checks):
    nodes = lambda r: f"{r['nodes']:,}" if r["status"] == "solved" else r["status"]
    cost = lambda r: (f"{r['cost']}" + (" ✗" if r["optimal"] is False else "")) if r["status"] == "solved" else r["status"]
    bstar = lambda r: str(r["b_star"]) if r["status"] == "solved" and r["b_star"] is not None else "-"
    parts = [
        "## Nodes expanded (deadlock pruning on)", pivot(rows, True, nodes),
        "## Nodes expanded (deadlock pruning off)", pivot(rows, False, nodes),
        "## Solution cost in pushes (✗ = not optimal, compared with UCS)", pivot(rows, True, cost),
        "## Effective branching factor b* (pruning on)", pivot(rows, True, bstar),
        "## Heuristic checks (A*): admissible = h(start) ≤ C*, violations of h(n) ≤ 1 + h(n')",
        "\n".join(["| Level | Heuristic | Pruning | h(start) | C* | Admissible | Consistency violations |",
                   "|---|---|---|---|---|---|---|",
                   *[f"| {c['level']} | {c['heur']} | {'on' if c['prune'] else 'off'} | {c['h_start']} | "
                     f"{c['c_star']} | {'yes' if c['admissible'] else 'NO'} | {c['violations']} |" for c in checks]]),
    ]
    return "\n\n".join(parts) + "\n"


def chart(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    levels = list(dict.fromkeys(r["level"] for r in rows))
    width = 0.8 / len(SETUPS)
    fig, ax = plt.subplots(figsize=(12, 5))
    for i, (algo, heur) in enumerate(SETUPS):
        ys = [next((r["nodes"] for r in rows if r["level"] == lv and r["algo"] == algo and r["heur"] == heur
                    and r["prune"] and r["status"] == "solved"), 0) for lv in levels]
        ax.bar([x + i * width for x in range(len(levels))], ys, width, label=setup_name(algo, heur))
    ax.set_yscale("log")
    ax.set_xticks([x + 0.4 - width / 2 for x in range(len(levels))], levels, rotation=20)
    ax.set_ylabel("Nodes expanded (log scale)")
    ax.set_title("Nodes expanded per level, deadlock pruning on (no bar = gave up)")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bridge.set_limits(NODE_LIMIT, TIME_LIMIT)
    levels = sorted(LEVELS_DIR.glob("*.txt"))
    rows = run_all(levels)
    write_csv(OUT / "runs.csv", rows)
    checks = verify_all(levels, rows)
    write_csv(OUT / "verify.csv", checks)
    (OUT / "tables.md").write_text(tables(rows, checks), encoding="utf-8")
    chart(rows, OUT / "nodes.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
