% Deadlock knowledge base (Ch.7). dead(S) is proved by backward chaining over
% definite clauses. All rules are sound: they never flag a solvable state.
:- module(deadlock, [compute_dead_squares/0, dead/1, dead_box/2, dead_square/2]).
:- use_module(level).
:- use_module(state, [reachable/3, delta/3]).
:- use_module(library(ordsets)).
:- use_module(library(lists)).
:- dynamic dead_square/2.

% Dead squares: "pull" a box backwards from every goal. A cell no pull reaches can
% never be pushed to a goal, so a box there is dead. Run once per level.
% Pulling ignores other boxes and agent reachability: that only adds live cells, so it stays sound.
compute_dead_squares :-
    retractall(dead_square(_, _)),
    agent(AX, AY),
    reachable(AX-AY, [], Floor),
    findall(X-Y, goal(X, Y), Gs0),
    sort(Gs0, Gs),
    pull(Gs, Gs, Live),
    forall(( member(X-Y, Floor), \+ ord_memberchk(X-Y, Live) ),
           assertz(dead_square(X, Y))).

% Box at C pulled one cell to N = C+d needs N and the agent's cell N+d to be free of walls.
pull([], Live, Live).
pull([X-Y|Stack], Seen, Live) :-
    findall(NX-NY,
            ( delta(_, DX, DY), NX is X + DX, NY is Y + DY,
              AX is NX + DX, AY is NY + DY,
              \+ wall(NX, NY), \+ wall(AX, AY),
              \+ ord_memberchk(NX-NY, Seen) ),
            Ns0),
    sort(Ns0, Ns),
    ord_union(Seen, Ns, Seen1),
    append(Ns, Stack, Stack1),
    pull(Stack1, Seen1, Live).

% KB: a state is dead if some box is on a dead square or in a corner.
dead(state(_, Boxes)) :- member(X-Y, Boxes), dead_box(X, Y), !.   % green cut: one proof is enough

dead_box(X, Y) :- dead_square(X, Y).
dead_box(X, Y) :- corner(X, Y).

% \+ goal/2 is over static facts only, so after grounding it is a fixed not_goal table
% and the clause stays definite.
corner(X, Y) :- \+ goal(X, Y), wall_v(X, Y), wall_h(X, Y).

wall_v(X, Y) :- Y1 is Y - 1, wall(X, Y1).
wall_v(X, Y) :- Y1 is Y + 1, wall(X, Y1).
wall_h(X, Y) :- X1 is X - 1, wall(X1, Y).
wall_h(X, Y) :- X1 is X + 1, wall(X1, Y).
