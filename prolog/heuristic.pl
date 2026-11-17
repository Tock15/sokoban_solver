% Heuristics, counted in pushes, 0 at the goal. Both are consistent (proofs in the plan, Section 5):
% one push moves one box one cell, so each changes by at most 1 = step cost.
:- module(heuristic, [h/3]).
:- use_module(level).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(aggregate)).

h(none, _, 0).
% h_sum: each box to its nearest goal (goals may be shared).
h(h_sum, state(_, Boxes), H) :-
    goals(Gs),
    foldl(nearest(Gs), Boxes, 0, H).
% h_match: each box to a different goal, cheapest assignment. Dominates h_sum.
% shortcut: tries every permutation (n!), fine up to ~6 boxes; use the Hungarian algorithm beyond that.
h(h_match, state(_, Boxes), H) :-
    goals(Gs),
    length(Boxes, N),
    aggregate_all(min(C),
                  ( permutation(Gs, P0), length(P, N), append(P, _, P0),
                    foldl(dist, Boxes, P, 0, C) ),
                  H).

goals(Gs) :- findall(X-Y, goal(X, Y), Gs).

nearest(Gs, B, A0, A) :-
    aggregate_all(min(D), (member(G, Gs), dist(B, G, 0, D)), M),
    A is A0 + M.

dist(X1-Y1, X2-Y2, A0, A) :- A is A0 + abs(X1 - X2) + abs(Y1 - Y2).
