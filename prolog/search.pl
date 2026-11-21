:- module(search, [search/6]).
:- use_module(library(heaps)).
:- use_module(library(assoc)).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(state).
:- use_module(heuristic).
:- use_module(deadlock).

search(ids, _, Prune, S0, Limits, Result) :-
    !,
    ids(S0, Prune, Limits, Result).
search(Algo, Heur, Prune, S0, Limits, Result) :-
    memberchk(Algo, [bfs, ucs, greedy, astar]),
    h(Heur, S0, H0),
    priority(Algo, 0, H0, 0, P0),
    singleton_heap(Heap, P0, node(S0, 0, H0, [])),
    empty_assoc(Closed),
    bf(Heap, Closed, ctx(Algo, Heur, Prune, Limits), 1, 0, 1, 0, Result).

priority(bfs, _, _, Seq, Seq).
priority(ucs, G, _, Seq, G-Seq).
priority(greedy, _, H, Seq, H-Seq).
priority(astar, G, H, Seq, F-Seq) :- F is G + H.

pruned(true, S) :- dead(S).

bf(Heap, Closed, Ctx, Seq, N, MaxF, V, Result) :-
    Ctx = ctx(_, _, _, limits(MaxNodes, Deadline)),
    Info = info(N, MaxF, V),
    (   N >= MaxNodes -> Result = failed(node_limit, Info)
    ;   get_time(Now), Now > Deadline -> Result = failed(timeout, Info)
    ;   get_from_heap(Heap, _, node(S, G, H, Path), Heap1)
    ->  (   get_assoc(S, Closed, _)
        ->  bf(Heap1, Closed, Ctx, Seq, N, MaxF, V, Result)
        ;   goal_state(S)
        ->  reverse(Path, Pushes), Result = found(Pushes, G, Info)
        ;   expand(S, G, H, Path, Heap1, Closed, Ctx, Seq, N, MaxF, V, Result)
        )
    ;   Result = failed(no_solution, Info)
    ).

expand(S, G, H, Path, Heap, Closed, Ctx, Seq, N, MaxF, V, Result) :-
    Ctx = ctx(Algo, Heur, Prune, _),
    put_assoc(S, Closed, true, Closed1),
    N1 is N + 1,
    G1 is G + 1,
    findall(S1-P,
            ( push(S, P, S1), \+ get_assoc(S1, Closed1, _), \+ pruned(Prune, S1) ),
            Children),
    (   Algo == bfs, member(S1-P, Children), goal_state(S1)
    ->
        reverse([P|Path], Pushes), Result = found(Pushes, G1, info(N1, MaxF, V))
    ;   foldl(add_child(Algo, Heur, G1, H, Path), Children, Heap-Seq-V, Heap1-Seq1-V1),
        heap_size(Heap1, Size),
        MaxF1 is max(MaxF, Size),
        bf(Heap1, Closed1, Ctx, Seq1, N1, MaxF1, V1, Result)
    ).

add_child(Algo, Heur, G1, H, Path, S1-P, Heap-Seq-V, Heap1-Seq1-V1) :-
    h(Heur, S1, H1),
    ( H > 1 + H1 -> V1 is V + 1 ; V1 = V ),
    priority(Algo, G1, H1, Seq, Pri),
    add_to_heap(Heap, Pri, node(S1, G1, H1, [P|Path]), Heap1),
    Seq1 is Seq + 1.

ids(S0, Prune, limits(MaxNodes, Deadline), Result) :-
    nb_setval(ids_nodes, 0),
    catch(ids_from(0, S0, Prune, MaxNodes, Deadline, Pushes, L),
          search_limit(Reason, L), true),
    nb_getval(ids_nodes, N),
    (   var(Reason)
    ->  length(Pushes, Cost), Result = found(Pushes, Cost, info(N, L, 0))
    ;   Result = failed(Reason, info(N, L, 0))
    ).

ids_from(L, S0, Prune, MaxNodes, Deadline, Pushes, Depth) :-
    (   dls(S0, L, [S0], Prune, lim(MaxNodes, Deadline, L), Pushes)
    ->  Depth = L
    ;   L1 is L + 1,
        ids_from(L1, S0, Prune, MaxNodes, Deadline, Pushes, Depth)
    ).

dls(S, _, _, _, _, []) :- goal_state(S), !.
dls(S, L, Path, Prune, Lim, [P|Ps]) :-
    L > 0,
    tick(Lim),
    push(S, P, S1),
    \+ pruned(Prune, S1),
    \+ memberchk(S1, Path),
    L1 is L - 1,
    dls(S1, L1, [S1|Path], Prune, Lim, Ps).

tick(lim(MaxNodes, Deadline, L)) :-
    nb_getval(ids_nodes, N0),
    N is N0 + 1,
    nb_setval(ids_nodes, N),
    (   N >= MaxNodes -> throw(search_limit(node_limit, L))
    ;   N mod 1000 =:= 0, get_time(Now), Now > Deadline -> throw(search_limit(timeout, L))
    ;   true
    ).
