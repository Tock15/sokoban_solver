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
