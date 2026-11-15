% Canonical state state(Region, Boxes), reachability, push/3, goal test.
% Cells are X-Y. Boxes is an ordset. Region is the smallest reachable cell in
% standard order (leftmost column, then top row), so all agent positions inside
% one region map to the same state.
:- module(state, [initial_state/1, reachable/3, push/3, goal_state/1, delta/3]).
:- use_module(level).
:- use_module(library(ordsets)).
:- use_module(library(lists)).

delta(u, 0, -1).
delta(d, 0, 1).
delta(l, -1, 0).
delta(r, 1, 0).

initial_state(state(R, Boxes)) :-
    agent(AX, AY),
    findall(X-Y, box(X, Y), Bs),
    sort(Bs, Boxes),
    canonical(AX-AY, Boxes, R).

canonical(Cell, Boxes, R) :-
    reachable(Cell, Boxes, [R|_]).

% reachable(+Start, +Boxes, -Cells): ordset of cells the agent can walk to without pushing.
% shortcut: assumes the level is enclosed by walls (flood never terminates otherwise); add a bounds check if open levels are used.
reachable(Start, Boxes, Cells) :-
    flood([Start], Boxes, [Start], Cells).

flood([], _, Seen, Seen).
flood([X-Y|Stack], Boxes, Seen, Cells) :-
    findall(NX-NY,
            ( delta(_, DX, DY), NX is X + DX, NY is Y + DY,
              free(NX-NY, Boxes), \+ ord_memberchk(NX-NY, Seen) ),
            Ns0),
    sort(Ns0, Ns),
    ord_union(Seen, Ns, Seen1),
    append(Ns, Stack, Stack1),
    flood(Stack1, Boxes, Seen1, Cells).

free(X-Y, Boxes) :-
    \+ wall(X, Y),
    \+ ord_memberchk(X-Y, Boxes).

% push(+State, -push(Box, Dir), -Next): one box push (step cost 1).
% Legal if the agent can reach the cell behind the box and the target cell is free.
% Dead-square pruning is applied by the search (Prune flag), not here.
push(state(R, Boxes), push(BX-BY, Dir), state(R1, Boxes1)) :-
    reachable(R, Boxes, Reach),
    member(BX-BY, Boxes),
    delta(Dir, DX, DY),
    PX is BX - DX, PY is BY - DY,
    ord_memberchk(PX-PY, Reach),
    TX is BX + DX, TY is BY + DY,
    free(TX-TY, Boxes),
    ord_del_element(Boxes, BX-BY, B0),
    ord_add_element(B0, TX-TY, Boxes1),
    canonical(BX-BY, Boxes1, R1).   % agent now stands where the box was

goal_state(state(_, Boxes)) :-
    forall(member(X-Y, Boxes), goal(X, Y)).
