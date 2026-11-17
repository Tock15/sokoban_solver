% Run: swipl -g run_tests -t halt tests/test_engine.pl
:- use_module('../prolog/verify').
:- use_module('../prolog/solver').
:- use_module('../prolog/level').
:- use_module('../prolog/state').
:- use_module('../prolog/heuristic').
:- use_module('../prolog/deadlock').
:- use_module(library(plunit)).

level('levels/01_tiny.txt', 2).
level('levels/02_two_boxes.txt', 4).
level('levels/03_three_boxes.txt', 6).

optimal_algo(bfs, none).
optimal_algo(ids, none).
optimal_algo(ucs, none).
optimal_algo(astar, h_sum).
optimal_algo(astar, h_match).

:- begin_tests(engine).

test(optimal_algorithms_find_optimal_cost,
     [forall((level(F, C), optimal_algo(A, H), member(P, [true, false])))]) :-
    solve(F, A, H, P, _, stats(_, _, Cost, _)),
    assertion(Cost == C).

test(greedy_solves_but_maybe_not_optimal, [forall((level(F, C), member(H, [h_sum, h_match])))]) :-
    solve(F, greedy, H, true, _, stats(_, _, Cost, _)),
    assertion(Cost >= C).

test(plan_replays_to_goal, [forall(level(F, _))]) :-
    solve(F, astar, h_match, true, Plan, _),
    agent(AX, AY),
    initial_state(state(_, B0)),
    foldl(replay, Plan, AX-AY-B0, _-_-B),
    assertion(forall(member(X-Y, B), goal(X, Y))).

test(heuristics_zero_at_goal_and_match_dominates, [forall(level(F, _))]) :-
    load_level(F),
    findall(X-Y, goal(X, Y), Gs0), sort(Gs0, Gs),
    h(h_sum, state(_, Gs), 0),
    h(h_match, state(_, Gs), 0),
    initial_state(S0),
    h(h_sum, S0, Hs), h(h_match, S0, Hm),
    assertion(Hm >= Hs).

test(consistent_and_admissible, [forall((level(F, _), member(H, [h_sum, h_match]), member(P, [true, false])))]) :-
    verify(F, H, P, report(_, _, Admissible, Violations)),
    assertion(Admissible == true),
    assertion(Violations == 0).

% Soundness: deadlock rules never flag a state on a known solution path.
test(deadlock_sound_on_solution_path, [forall(level(F, _))]) :-
    run(F, ucs, none, false, found(Pushes, _, _), _),
    initial_state(S0),
    foldl(apply_push, Pushes, S0, _).

test(corner_and_dead_square_detected) :-
    load_level('levels/01_tiny.txt'),
    compute_dead_squares,
    assertion(dead(state(_, [1-1]))),     % corner, not a goal
    assertion(dead(state(_, [2-1]))),     % along top wall, no goal on it
    assertion(\+ dead(state(_, [2-2]))),
    assertion(dead(state(_, [4-1]))),     % corner next to the goal
    assertion(\+ dead(state(_, [3-2]))).

:- end_tests(engine).

apply_push(P, S, S1) :-
    assertion(\+ dead(S)),
    once(push(S, P, S1)).

replay(M, X-Y-B, NX-NY-B1) :-
    delta(M, DX, DY),
    NX is X + DX, NY is Y + DY,
    (   memberchk(NX-NY, B)
    ->  BX is NX + DX, BY is NY + DY,
        \+ wall(BX, BY), \+ memberchk(BX-BY, B),
        selectchk(NX-NY, B, B0), B1 = [BX-BY|B0]
    ;   \+ wall(NX, NY), B1 = B
    ).
