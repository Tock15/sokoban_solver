:- module(level, [load_level/1, wall/2, goal/2, box/2, agent/2]).
:- dynamic wall/2, goal/2, box/2, agent/2.

load_level(File) :-
    retractall(wall(_, _)), retractall(goal(_, _)),
    retractall(box(_, _)), retractall(agent(_, _)),
    read_file_to_string(File, Text, []),
    split_string(Text, "\n", "\r", Lines),
    forall(nth0(Y, Lines, Line),
           ( string_chars(Line, Cs),
             forall(nth0(X, Cs, C), cell(C, X, Y)) )).

cell('#', X, Y) :- assertz(wall(X, Y)).
cell('.', X, Y) :- assertz(goal(X, Y)).
cell('$', X, Y) :- assertz(box(X, Y)).
cell('*', X, Y) :- assertz(box(X, Y)), assertz(goal(X, Y)).
cell('@', X, Y) :- assertz(agent(X, Y)).
cell('+', X, Y) :- assertz(agent(X, Y)), assertz(goal(X, Y)).
cell(C, _, _) :- \+ memberchk(C, ['#', '.', '$', '*', '@', '+']).
