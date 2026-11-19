## Nodes expanded (deadlock pruning on)

| Level | Boxes | BFS | IDS | UCS | GREEDY h_sum | GREEDY h_match | ASTAR h_sum | ASTAR h_match |
|---|---|---|---|---|---|---|---|---|
| 01_tiny | 1 | 2 | 3 | 2 | 2 | 2 | 2 | 2 |
| 02_two_boxes | 2 | 18 | 36 | 25 | 6 | 5 | 20 | 15 |
| 03_three_boxes | 3 | 97 | 725 | 149 | 6 | 6 | 26 | 26 |
| 04_gap_three_boxes | 3 | 748 | node_limit | 769 | 31 | 30 | 650 | 557 |
| 05_four_boxes | 4 | 1,736 | node_limit | 1,799 | 32 | 21 | 650 | 296 |
| 06_detour | 3 | 302 | node_limit | 325 | 41 | 51 | 169 | 155 |
| 07_crossroads | 4 | 1,043 | node_limit | 1,554 | 148 | 85 | 190 | 131 |
| 08_long_haul | 4 | 8,901 | node_limit | 9,402 | 165 | 69 | 3,390 | 1,862 |
| 09_open_room | 4 | 5,882 | node_limit | 5,951 | 38 | 63 | 4,230 | 2,438 |
| 10_five_boxes | 5 | node_limit | node_limit | node_limit | 1,481 | 93 | node_limit | 15,836 |

## Nodes expanded (deadlock pruning off)

| Level | Boxes | BFS | IDS | UCS | GREEDY h_sum | GREEDY h_match | ASTAR h_sum | ASTAR h_match |
|---|---|---|---|---|---|---|---|---|
| 01_tiny | 1 | 5 | 6 | 9 | 2 | 2 | 2 | 2 |
| 02_two_boxes | 2 | 64 | 123 | 124 | 6 | 5 | 20 | 15 |
| 03_three_boxes | 3 | 581 | 4,727 | 1,150 | 6 | 6 | 26 | 26 |
| 04_gap_three_boxes | 3 | 7,506 | node_limit | 7,709 | 38 | 1,362 | 3,048 | 2,341 |
| 05_four_boxes | 4 | node_limit | node_limit | node_limit | 32 | 21 | 1,122 | 296 |
| 06_detour | 3 | 1,840 | node_limit | 2,241 | 48 | 70 | 316 | 282 |
| 07_crossroads | 4 | 1,779 | node_limit | 2,965 | 353 | 169 | 231 | 147 |
| 08_long_haul | 4 | node_limit | node_limit | node_limit | 295 | 1,927 | 10,352 | 3,988 |
| 09_open_room | 4 | node_limit | node_limit | node_limit | 46 | 128 | 11,718 | 2,438 |
| 10_five_boxes | 5 | node_limit | node_limit | node_limit | 3,024 | 126 | node_limit | 15,836 |

## Solution cost in pushes (✗ = not optimal, compared with UCS)

| Level | Boxes | BFS | IDS | UCS | GREEDY h_sum | GREEDY h_match | ASTAR h_sum | ASTAR h_match |
|---|---|---|---|---|---|---|---|---|
| 01_tiny | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 02_two_boxes | 2 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 03_three_boxes | 3 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| 04_gap_three_boxes | 3 | 18 | node_limit | 18 | 18 | 18 | 18 | 18 |
| 05_four_boxes | 4 | 13 | node_limit | 13 | 17 ✗ | 17 ✗ | 13 | 13 |
| 06_detour | 3 | 10 | node_limit | 10 | 14 ✗ | 16 ✗ | 10 | 10 |
| 07_crossroads | 4 | 8 | node_limit | 8 | 10 ✗ | 10 ✗ | 8 | 8 |
| 08_long_haul | 4 | 24 | node_limit | 24 | 26 ✗ | 24 | 24 | 24 |
| 09_open_room | 4 | 18 | node_limit | 18 | 20 ✗ | 20 ✗ | 18 | 18 |
| 10_five_boxes | 5 | node_limit | node_limit | node_limit | 21 | 27 | node_limit | 21 |

## Effective branching factor b* (pruning on)

| Level | Boxes | BFS | IDS | UCS | GREEDY h_sum | GREEDY h_match | ASTAR h_sum | ASTAR h_match |
|---|---|---|---|---|---|---|---|---|
| 01_tiny | 1 | 1.0 | 1.303 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| 02_two_boxes | 2 | 1.704 | 2.114 | 1.891 | 1.169 | 1.091 | 1.763 | 1.607 |
| 03_three_boxes | 3 | 1.899 | 2.784 | 2.067 | 1.0 | 1.0 | 1.441 | 1.441 |
| 04_gap_three_boxes | 3 | 1.339 | - | 1.341 | 1.055 | 1.052 | 1.326 | 1.313 |
| 05_four_boxes | 4 | 1.653 | - | 1.658 | 1.067 | 1.023 | 1.515 | 1.41 |
| 06_detour | 3 | 1.607 | - | 1.621 | 1.135 | 1.127 | 1.499 | 1.483 |
| 07_crossroads | 4 | 2.212 | - | 2.337 | 1.475 | 1.375 | 1.733 | 1.639 |
| 08_long_haul | 4 | 1.385 | - | 1.388 | 1.119 | 1.077 | 1.323 | 1.285 |
| 09_open_room | 4 | 1.527 | - | 1.528 | 1.058 | 1.1 | 1.496 | 1.445 |
| 10_five_boxes | 5 | - | - | - | 1.324 | 1.079 | - | 1.504 |

## Heuristic checks (A*): admissible = h(start) ≤ C*, violations of h(n) ≤ 1 + h(n')

| Level | Heuristic | Pruning | h(start) | C* | Admissible | Consistency violations |
|---|---|---|---|---|---|---|
| 01_tiny | h_sum | on | 2 | 2 | yes | 0 |
| 01_tiny | h_sum | off | 2 | 2 | yes | 0 |
| 01_tiny | h_match | on | 2 | 2 | yes | 0 |
| 01_tiny | h_match | off | 2 | 2 | yes | 0 |
| 02_two_boxes | h_sum | on | 4 | 4 | yes | 0 |
| 02_two_boxes | h_sum | off | 4 | 4 | yes | 0 |
| 02_two_boxes | h_match | on | 4 | 4 | yes | 0 |
| 02_two_boxes | h_match | off | 4 | 4 | yes | 0 |
| 03_three_boxes | h_sum | on | 6 | 6 | yes | 0 |
| 03_three_boxes | h_sum | off | 6 | 6 | yes | 0 |
| 03_three_boxes | h_match | on | 6 | 6 | yes | 0 |
| 03_three_boxes | h_match | off | 6 | 6 | yes | 0 |
| 04_gap_three_boxes | h_sum | on | 12 | 18 | yes | 0 |
| 04_gap_three_boxes | h_sum | off | 12 | 18 | yes | 0 |
| 04_gap_three_boxes | h_match | on | 14 | 18 | yes | 0 |
| 04_gap_three_boxes | h_match | off | 14 | 18 | yes | 0 |
| 05_four_boxes | h_sum | on | 11 | 13 | yes | 0 |
| 05_four_boxes | h_match | on | 13 | 13 | yes | 0 |
| 06_detour | h_sum | on | 7 | 10 | yes | 0 |
| 06_detour | h_sum | off | 7 | 10 | yes | 0 |
| 06_detour | h_match | on | 8 | 10 | yes | 0 |
| 06_detour | h_match | off | 8 | 10 | yes | 0 |
| 07_crossroads | h_sum | on | 6 | 8 | yes | 0 |
| 07_crossroads | h_sum | off | 6 | 8 | yes | 0 |
| 07_crossroads | h_match | on | 6 | 8 | yes | 0 |
| 07_crossroads | h_match | off | 6 | 8 | yes | 0 |
| 08_long_haul | h_sum | on | 18 | 24 | yes | 0 |
| 08_long_haul | h_match | on | 20 | 24 | yes | 0 |
| 09_open_room | h_sum | on | 13 | 18 | yes | 0 |
| 09_open_room | h_match | on | 18 | 18 | yes | 0 |
