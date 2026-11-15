# Autonomous Sokoban Solver — Project Plan

**Course:** 01286342 Artificial Intelligence
**Team:** Koses Suvarnasuddhi (67011152), Ekboonya Srisook (67011110)
**Stack:** SWI-Prolog (AI engine) + Python / Pygame (GUI) via PySwip
**Due:** Sun 22 / Mon 23 Nov 2026 (9 days from Sat 14 Nov)

> This plan is separate from the original proposal. It adds the course topics the proposal doesn't yet cover and fixes the claims that need precise definitions before the presentation.

---

## 1. Goal

Build a Sokoban solver in which **Prolog performs all reasoning and search**. The project must:

1. Find **push-optimal** solutions with A* graph search.
2. Prove (on paper) and verify (in code) that the heuristics are **admissible and consistent**.
3. Prune deadlocks using a **sound** knowledge base of definite clauses.
4. Compare uninformed and informed search on the same levels, with measured results.
5. Animate the solution in a Python GUI.

---

## 2. Mapping to course topics

| Course topic | Where it appears in the project |
|---|---|
| Prolog + cut | Whole engine. Cuts used deliberately and labelled green or red in the code |
| Ch.3 Problem formulation | State, actions, transition model, goal test, cost (Section 3) |
| Ch.3 BFS | Agent walking paths between pushes, plus a baseline solver |
| Ch.3 DFS / IDS | Baseline solvers (depth-limited) |
| Ch.3 Uniform Cost Search | Baseline, and ground truth for the optimal cost |
| Ch.3 Graph search vs tree search | Closed set over canonical states |
| Best-first (greedy) | Comparison: fast but not optimal |
| A* | Main solver |
| Admissibility, consistency, dominance, effective branching factor (b*) | Heuristic proofs + experiments (Sections 5, 7) |
| Ch.7 KB, entailment, Horn/definite clauses (to 7.5.3) | Deadlock rules as a definite-clause KB: `KB ⊨ dead(S)` |
| Ch.6 Minimax / alpha-beta | **Not used, deliberately.** Sokoban has one agent and no opponent, so adversarial search does not apply |

---

## 3. Problem formulation

**Cost model: 1 per box push.** Agent walking between pushes is free in the search and is computed afterwards by BFS for the animation.

| Component | Definition |
|---|---|
| State | `state(AgentRegion, Boxes)`. `Boxes` is a **sorted** list of cells; `AgentRegion` is the canonical (top-left-most) cell the agent can reach without pushing |
| Static facts | `wall(X,Y)`, `goal(X,Y)`, `dead_square(X,Y)` (precomputed) |
| Actions | `push(Box, Dir)`: legal if the agent can reach the cell behind the box, and the destination is not a wall, a box, or a dead square |
| Transition | The box moves one cell; the agent stands where the box was; the reachable region is recomputed |
| Goal test | Every box is on a goal |
| Step cost | 1 per push |

**Why canonical states:** two states that differ only in where the agent stands inside the same region are the same search state. Merging them reduces the state space a lot and makes the closed set work properly.

**Two-level search:**
- **Macro level:** A* over pushes (the expensive search).
- **Micro level:** BFS on the grid to walk the agent to the push position (cheap; used to turn the plan into individual moves for the GUI).

---

## 4. Search algorithms to implement (Prolog)

| Algorithm | Frontier | Optimal for push cost? | Role |
|---|---|---|---|
| BFS | FIFO queue | Yes (uniform cost 1) | Baseline |
| DFS (depth-limited) | Stack | No | Baseline (shows why DFS fails) |
| IDS | Repeated depth-limited DFS | Yes | Baseline |
| UCS | Priority on g | Yes | Ground truth for optimal cost |
| Greedy best-first | Priority on h | No | Contrast with A* |
| **A\*** | Priority on f = g + h | **Yes (with a consistent h)** | Main solver |

**Data structures (SWI-Prolog):**
- Frontier: `library(heaps)` (priority queue)
- Closed set: `library(assoc)` keyed on the canonical state
- Avoid plain lists for these, since lookups would be O(n)

---

## 5. Heuristics and proofs

All distances are counted in pushes. Each heuristic is 0 at the goal.

### h1 — Sum of nearest-goal Manhattan distances (`h_sum`)
`h_sum(n) = Σ_box min_goal manhattan(box, goal)`

**Consistency proof.** A push moves one box one cell. By the triangle inequality, that box's term changes by at most 1, and the other terms don't change. So
`h(n) ≤ 1 + h(n') = c(n, a, n') + h(n')`.
With h(goal) = 0, consistency implies admissibility.

### h2 — Minimum-cost matching (`h_match`)
Assign each box to a **different** goal so that the total Manhattan distance is as small as possible.

**Consistency proof.** Take the optimal assignment at n'. Using that same assignment at n costs at most 1 more, because only one box moved one cell. So `h(n) ≤ h(n') + 1`.

**Implementation:** with 5 or fewer boxes, try every permutation (5! = 120). No Hungarian algorithm needed.

### Dominance
`h_match ≥ h_sum` for every state, because `h_sum` is the same problem with the "different goals" constraint removed. So A* with `h_match` never expands more nodes than A* with `h_sum` (AIMA 3.6.1).

### h3 (stretch) — Push distance
Replace Manhattan distance with the BFS distance needed to **push** a box to a goal, ignoring other boxes. This is still admissible and consistent (same argument), and it accounts for walls.

### Empirical verification (in code)
- **Consistency:** for every expanded edge, check `h(n) ≤ c + h(n')` and log any violation. Target: zero violations on every level.
- **Admissibility:** check `h(start) ≤ C*`, where C* is the optimal cost found by UCS.

---

## 6. Deadlock knowledge base (Ch.7 link)

Deadlock rules are written as **definite clauses** (Horn clauses with exactly one positive literal). Prolog answers `dead(S)` by **backward chaining**. Because the grid is finite, the first-order rules can be grounded into propositional definite clauses, which links them to Ch.7.

| Rule | Soundness |
|---|---|
| **Dead squares** (precomputed): "pull" a box backwards from every goal; any cell never reached is dead | Sound by construction: a box on such a cell can never reach a goal |
| **Corner deadlock:** box not on a goal, with walls on two adjacent sides | Sound |
| **Wall deadlock** (future work, cut for the deadline): box against a wall segment that is closed by corners at both ends and has no goal on it | Sound **only** with the "closed at both ends" condition. The naive version is wrong. Note: dead squares already cover most of these cases |
| **Freeze deadlock** (future work): e.g. a 2×2 block of boxes/walls containing a box not on a goal | Sound |

**Optimality argument:** pruning a state that can't reach a goal is equivalent to giving it h = ∞. Admissibility and consistency are preserved, so A* stays optimal and complete.

**Rule:** a deadlock rule must never flag a solvable state. Unit-test every rule on states that are known to be solvable.

---

## 7. Experiments

**Levels:** about 8 levels of increasing difficulty (e.g. from the Microban set), from 1 to about 4 boxes.

**Configurations:**
- BFS, IDS, UCS, Greedy, A* + h_sum, A* + h_match (+ h3 if done)
- Each one **with and without** deadlock pruning

**Metrics:**
| Metric | Purpose |
|---|---|
| Nodes expanded | Main measure of efficiency |
| Peak frontier size | Memory |
| Time (ms) | Practical speed |
| Solution cost (pushes) | Optimality check: should equal UCS cost for the optimal algorithms |
| Effective branching factor b* | From N + 1 = 1 + b* + (b*)² + … + (b*)^d (AIMA 3.6.1) |
| Consistency violations | Should be 0 |

**Expected results to discuss:**
- A* + h_match expands fewer nodes than A* + h_sum (dominance).
- Greedy is fast but sometimes finds non-optimal solutions.
- DFS/IDS blow up or time out on medium levels.
- Deadlock pruning reduces node counts on every algorithm.
- Honest limit: plain Prolog is expected to handle about 3–5 boxes.

Use a timeout (e.g. 60 s) and node limit, and report unsolved levels as "timeout" rather than leaving them out.

---

## 8. Use of cut

| Where | Cut type | Reason |
|---|---|---|
| Deadlock checks (`dead(S) :- corner(S), !.`) | Green | Stop after the first proof; doesn't change which answers are true |
| Goal test in the search loop | Green | Stop at the first goal popped (A* guarantees it is optimal) |
| Choosing between `push` and walls in move generation | Possibly red | If used, comment why and what breaks without it |

Be ready to explain the difference: removing a **green** cut changes only efficiency; removing a **red** cut changes the answers.

---

## 9. System architecture

```
Python (Pygame GUI)
  ├─ level picker, algorithm + heuristic picker, pruning toggle
  ├─ animates moves, shows metrics table
  └─ PySwip ──► Prolog query: solve(Level, Algo, Heur, Prune, Plan, Stats)

SWI-Prolog engine
  ├─ level.pl       : facts (wall/goal/box/agent)
  ├─ state.pl       : canonical state, reachability (BFS)
  ├─ search.pl      : BFS, DFS, IDS, UCS, Greedy, A*
  ├─ heuristic.pl   : h_sum, h_match, (h_push)
  ├─ deadlock.pl    : dead squares + deadlock rules (definite clauses)
  └─ verify.pl      : consistency/admissibility checks, stats
```

The Prolog engine returns the push plan plus statistics. Python only displays results and contains **no search logic**.

---

## 10. Timeline — 9 days (Sat 14 → Sun 22 Nov)

### Scope for the deadline

| Status | Items |
|---|---|
| **Must have** | Canonical state + `push`, A* + h_sum, dead squares + corner deadlock, GUI animation, consistency check, results table |
| **Should have** | h_match (permutations), UCS / BFS / Greedy baselines, IDS with a timeout |
| **Cut** | Wall deadlock, freeze deadlock, push-distance heuristic (h3), plain DFS. Mention these as future work |

**Shortcut:** write **one generic best-first search** that takes a priority function. Then
`UCS: f = g`, `Greedy: f = h`, `A*: f = g + h` are the same code, so three algorithms cost the effort of one.

### Split the work (in parallel from day 1)

- **Person A — Prolog engine:** state, actions, search, heuristics, deadlocks, verification
- **Person B — Python side:** level files, Pygame GUI, PySwip bridge, experiment runner script, report/slides. Start the GUI with a **hard-coded fake plan** so it doesn't wait for the engine

Agree on the interface on day 1 and don't change it:
`solve(LevelFile, Algo, Heur, Prune, Plan, Stats)` where `Plan` is a list of moves (`u/d/l/r`) and `Stats` holds nodes, time, cost, max_frontier.

### Day by day

| Day | Person A (Prolog) | Person B (Python) |
|---|---|---|
| **Sat 14** | Level → facts, canonical state, reachability BFS, `push/3` | Pick ~8 levels (1–4 boxes), level file format, Pygame board drawing |
| **Sun 15** | Generic best-first + heaps + assoc closed set; A* + h_sum solves the tiny levels | Animate a fake plan; level/algorithm/heuristic pickers |
| **Mon 16** | Dead squares + corner deadlock + unit tests on solvable states; turn the push plan into moves (BFS walk) | PySwip bridge: call `solve/6`, show the real plan |
| **Tue 17** | h_match (permutations); UCS / Greedy / BFS via the generic search; IDS with a node limit | Stats panel in GUI; experiment runner (all configs × levels → CSV) |
| **Wed 18** | Verification: consistency check per edge, h(start) ≤ C*; fix bugs | **Integration day:** full pipeline working end to end |
| **Thu 19** | **Feature freeze.** Run experiments, fix crashes only | Results table + b* calculation; chart of nodes expanded |
| **Fri 20** | Write proofs + deadlock soundness section of report | Report structure, screenshots, slides draft |
| **Sat 21** | Both: finish report and slides | |
| **Sun 22** | Both: rehearse Q&A (Section 11), live-demo practice, buffer for submission | |

**If behind on Wed 18:** drop IDS and h_match, keep A* + h_sum + UCS (needed for the optimal-cost check) + Greedy. That is still enough for every Q&A item in Section 11.

---

## 11. Presentation Q&A preparation

| Likely question | Answer outline |
|---|---|
| Why is your heuristic admissible? | Consistent + h(goal) = 0 ⇒ admissible. Also checked h(start) ≤ C* on every level |
| Why is it consistent? | One push moves one box one cell ⇒ h changes by at most 1 = step cost (proofs in Section 5) |
| Does deadlock pruning break optimality? | No: only provably dead states are pruned, equivalent to h = ∞ |
| Which heuristic is better and why? | h_match dominates h_sum ⇒ never more expansions; show the node-count table |
| Greedy vs A*: which is optimal? | A* (f = g + h, consistent h). Greedy ignores g, so it can return longer solutions; show an example level |
| Why graph search, not tree search? | Boxes can be pushed back and forth, giving repeated states; the closed set avoids re-expanding them |
| Why push cost instead of move cost? | Standard in Sokoban research; it makes the state space smaller and the heuristic proofs clean. Walking is solved optimally by BFS afterwards |
| Where is the logic chapter? | Deadlock KB = definite clauses; Prolog proves `dead(S)` by backward chaining (KB ⊨ dead(S)) |
| Where do you use cut? Green or red? | Section 8 |
| Why no minimax? | Single-agent, deterministic, fully observable problem: no opponent to model |
| What are the limits? | Exponential state space; Prolog handles about 3–5 boxes; stronger solvers need macro moves and pattern databases (future work) |
