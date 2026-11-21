:- module(solver, [solve/6, run/6, dead_boxes/3]).
:- use_module(level).
:- use_module(state).
:- use_module(search).
:- use_module(deadlock).

:- dynamic limit/2.
limit(nodes, 1000000).
limit(seconds, 60).

solve(LevelFile, Algo, Heur, Prune, Plan, stats(Nodes, TimeMs, Cost, MaxF)) :-
    run(LevelFile, Algo, Heur, Prune, Result, TimeMs),
    result(Result, Plan, Nodes, Cost, MaxF).

run(LevelFile, Algo, Heur0, Prune, Result, TimeMs) :-
    load_level(LevelFile),
    compute_dead_squares,
    initial_state(S0),
    ( memberchk(Algo, [greedy, astar]) -> Heur = Heur0 ; Heur = none ),
    limit(nodes, MaxNodes),
    limit(seconds, Secs),
    get_time(T0),
    Deadline is T0 + Secs,
    search(Algo, Heur, Prune, S0, limits(MaxNodes, Deadline), Result),
    get_time(T1),
    TimeMs is round((T1 - T0) * 1000).

result(found(Pushes, Cost, info(N, F, _)), Moves, N, Cost, F) :-
    agent(AX, AY),
    initial_state(state(_, Boxes)),
    plan_moves(AX-AY, Boxes, Pushes, Moves).
result(failed(Reason, info(N, F, _)), [], N, Reason, F).

dead_boxes(LevelFile, Boxes, Dead) :-
    load_level(LevelFile),
    compute_dead_squares,
    include([[X, Y]]>>dead_box(X, Y), Boxes, Dead).
