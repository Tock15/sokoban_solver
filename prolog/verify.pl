% Empirical checks of the heuristic proofs (plan Section 5).
%   Consistency : violations of h(n) =< 1 + h(n') counted on every edge A* expands (target 0)
%   Admissibility: h(start) =< C*, where C* is the optimal cost found by UCS
% verify(+LevelFile, +Heur, +Prune, -report(HStart, CStar, Admissible, Violations))
% Load this file (it loads solver.pl) to get both solve/6 and verify/4.
:- module(verify, [verify/4]).
:- use_module(solver).
:- use_module(state).
:- use_module(heuristic).

verify(LevelFile, Heur, Prune, report(H0, CStar, Admissible, V)) :-
    run(LevelFile, ucs, none, Prune, found(_, CStar, _), _),
    run(LevelFile, astar, Heur, Prune, found(_, _, info(_, _, V)), _),
    initial_state(S0),
    h(Heur, S0, H0),
    ( H0 =< CStar -> Admissible = true ; Admissible = false ).
