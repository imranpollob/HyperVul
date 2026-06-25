# Generic Baseline View Inspection

These views are for RQ1 generic baselines and do not use a HyperVul hyperedge builder.

## Function And Sequence Views

| Split | Function Examples | Function Pos | Function Neg | Sequence Graphs | Sequence Tokens |
|---|---:|---:|---:|---:|---:|
| train | 10740 | 215 | 10525 | 1614 | 10740 |
| val | 844 | 38 | 806 | 167 | 844 |
| test | 773 | 41 | 732 | 138 | 773 |

## Generic Graph Views

| Split | View | Graphs | Nodes | Edges | Pos | Neg | Edge Types |
|---|---|---:|---:|---:|---:|---:|---|
| train | callgraph_view | 1614 | 12221 | 12552 | 215 | 10525 | call:12552 |
| train | pairwise_graph_view | 1614 | 12221 | 51277 | 215 | 10525 | shared_state:30255, call:12552, shared_callee:8470 |
| val | callgraph_view | 167 | 987 | 1078 | 38 | 806 | call:1078 |
| val | pairwise_graph_view | 167 | 987 | 4343 | 38 | 806 | shared_state:2512, call:1078, shared_callee:753 |
| test | callgraph_view | 138 | 945 | 1294 | 41 | 732 | call:1294 |
| test | pairwise_graph_view | 138 | 945 | 4639 | 41 | 732 | shared_state:2269, call:1294, shared_callee:1076 |
