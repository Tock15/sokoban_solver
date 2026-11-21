:- use_module('../prolog/level').
:- use_module('../prolog/state').
:- use_module(library(plunit)).

tiny :- load_level('levels/01_tiny.txt').

:- begin_tests(state).

test(initial, [setup(tiny)]) :-
    initial_state(S),
    assertion(S == state(1-1, [2-2])).

test(pushes_from_start, [setup(tiny)]) :-
    initial_state(S),
    findall(D, push(S, push(_, D), _), Ds),
    msort(Ds, Sorted),
    assertion(Sorted == [d, l, r, u]).

test(solve_by_two_pushes_right, [setup(tiny)]) :-
    initial_state(S0),
    \+ goal_state(S0),
    push(S0, push(2-2, r), S1),
    push(S1, push(3-2, r), S2),
    assertion(goal_state(S2)).

test(canonical_merges_agent_positions, [setup(tiny)]) :-
    reachable(4-3, [2-2], Cells),
    assertion(Cells = [1-1|_]).

test(no_push_into_wall) :-
    load_level('levels/01_tiny.txt'),
    \+ push(state(1-1, [4-2]), push(4-2, r), _).

:- end_tests(state).
