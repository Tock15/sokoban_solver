% Entry point called from Python via PySwip.
% Interface (frozen day 1, do not change):
%   solve(+LevelFile, +Algo, +Heur, +Prune, -Plan, -Stats)
%   Algo  : bfs | ids | ucs | greedy | astar
%   Heur  : h_sum | h_match
%   Prune : true | false
%   Plan  : list of u/d/l/r
%   Stats : stats(Nodes, TimeMs, Cost, MaxFrontier)
:- module(solver, [solve/6]).
:- use_module(level).
:- use_module(state).
:- use_module(search).
:- use_module(heuristic).
:- use_module(deadlock).
:- use_module(verify).

% shortcut: fake plan so the GUI can be built before the engine; replace with search:search/... (Sun 15)
solve(LevelFile, _Algo, _Heur, _Prune, [r, r], stats(0, 0, 2, 0)) :-
    load_level(LevelFile).
