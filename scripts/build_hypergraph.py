"""
Contract-scoped hypergraph construction for HyperVul.

Each interaction (one function's {function, accessed state vars, external callees})
is a HYPEREDGE. Within a contract, hyperedges that touch the same state variable or
the same callee share a NODE -> this is what links multi-step interactions and what a
pairwise-edge expansion fragments.

We build directly from the already-extracted *_features.json items (which carry both
entity names AND their SmartBERT embeddings), so no AST re-run / re-encoding is needed.

A ContractGraph holds:
  node_feats : (Nn, 768) float32   - node embeddings (func / state / callee nodes)
  node_types : (Nn,) long          - 0=func, 1=state, 2=callee
  inc_node   : (E,) long  } incidence pairs (node i belongs to hyperedge e):
  inc_edge   : (E,) long  }   parallel arrays, one entry per (node, hyperedge) membership
  edge_label : (He,) float32       - per-hyperedge label
  edge_gidx  : (He,) long          - original item index (for metric parity with the flat split)
  edge_vtype : list[str]           - per-hyperedge vulnerability type
  edge_cross : (He,) bool          - is_cross_contract flag

`build_contract_graphs(items)` returns list[ContractGraph]. Grouping key keeps augmented
variants separate via source_id so training variants don't collapse into one mega-graph.
"""
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

NODE_FUNC, NODE_STATE, NODE_CALLEE = 0, 1, 2
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")


@dataclass
class ContractGraph:
    node_feats: np.ndarray
    node_types: np.ndarray
    inc_node: np.ndarray
    inc_edge: np.ndarray
    edge_label: np.ndarray
    edge_gidx: np.ndarray
    edge_vtype: list = field(default_factory=list)
    edge_cross: np.ndarray = None

    @property
    def num_nodes(self):
        return self.node_feats.shape[0]

    @property
    def num_edges(self):
        return self.edge_label.shape[0]


def _callee_index(item):
    """Map each external_call (by its position) to a stable callee key + its embedding."""
    nf_calls = item["node_features"]["external_calls"]  # [{call_text, embedding}]
    meta_calls = item.get("external_calls") or []        # dicts OR plain call_text strings
    by_text = {c["call_text"]: c["embedding"] for c in nf_calls}
    meta_by_text = {}
    for mc in meta_calls:
        if isinstance(mc, dict):
            meta_by_text[mc.get("call_text")] = (mc.get("receiver") or "", mc.get("method") or "")
    out = []
    for c in nf_calls:
        ct = c["call_text"]
        recv, meth = meta_by_text.get(ct, ("", ""))
        out.append(((recv, meth, ct[:40]), c["embedding"]))
    return out


def build_contract_graphs(items, group_keep_variant=True, drop_func=False):
    groups = defaultdict(list)
    for gidx, it in enumerate(items):
        fp = it.get("file") or it.get("filePath")
        cn = it.get("contract") or ""
        key = (it.get("source_id") if group_keep_variant else None, fp, cn)
        groups[key].append((gidx, it))

    graphs = []
    for key, members in groups.items():
        node_feats, node_types = [], []
        state_node = {}   # state var name -> node idx
        callee_node = {}  # callee key   -> node idx
        inc_node, inc_edge = [], []
        edge_label, edge_gidx, edge_vtype, edge_cross = [], [], [], []

        def add_node(emb, ntype):
            node_feats.append(emb)
            node_types.append(ntype)
            return len(node_feats) - 1

        for e_local, (gidx, it) in enumerate(members):
            members_nodes = []
            # function node (unique per interaction) — its embedding is the full function
            # source, which textually contains the call/state text. drop_func removes it to
            # force the interaction signal through the atomic state/callee nodes + structure.
            if not drop_func:
                members_nodes.append(add_node(it["node_features"]["function"], NODE_FUNC))
            # state-var nodes (shared by name within contract)
            sv_map = it["node_features"]["state_vars"]
            for sv_name in (it.get("state_vars_accessed") or []):
                if sv_name not in sv_map:
                    continue
                if sv_name not in state_node:
                    state_node[sv_name] = add_node(sv_map[sv_name], NODE_STATE)
                members_nodes.append(state_node[sv_name])
            # callee nodes (shared by (receiver,method) within contract)
            for ckey, cemb in _callee_index(it):
                if ckey not in callee_node:
                    callee_node[ckey] = add_node(cemb, NODE_CALLEE)
                members_nodes.append(callee_node[ckey])

            members_nodes = sorted(set(members_nodes))
            for n in members_nodes:
                inc_node.append(n)
                inc_edge.append(e_local)
            edge_label.append(float(it.get("label", 0.0)))
            edge_gidx.append(gidx)
            edge_vtype.append(it.get("vtype") or "Unknown")
            edge_cross.append(bool(it.get("is_cross_contract", False)))

        graphs.append(ContractGraph(
            node_feats=np.asarray(node_feats, dtype=np.float32),
            node_types=np.asarray(node_types, dtype=np.int64),
            inc_node=np.asarray(inc_node, dtype=np.int64),
            inc_edge=np.asarray(inc_edge, dtype=np.int64),
            edge_label=np.asarray(edge_label, dtype=np.float32),
            edge_gidx=np.asarray(edge_gidx, dtype=np.int64),
            edge_vtype=edge_vtype,
            edge_cross=np.asarray(edge_cross, dtype=bool),
        ))
    return graphs


def summarize(graphs, name):
    ne = sum(g.num_edges for g in graphs)
    nn = sum(g.num_nodes for g in graphs)
    shared = 0
    for g in graphs:
        deg = defaultdict(int)
        for n in g.inc_node:
            deg[n] += 1
        # a hyperedge is "linked" if any of its nodes is shared (degree>1)
        node_shared = {n for n, d in deg.items() if d > 1}
        for e in range(g.num_edges):
            members = g.inc_node[g.inc_edge == e]
            if any(m in node_shared for m in members):
                shared += 1
    print(f"[{name}] graphs={len(graphs)} hyperedges={ne} nodes={nn} "
          f"linked={shared}/{ne} ({100*shared/ne:.0f}%) avg_nodes/edge={g and (sum(len(gg.inc_edge) for gg in graphs)/ne):.1f}")


if __name__ == "__main__":
    splits = PROJECT_ROOT / "data" / "splits"
    for s in ["val_features.json", "test_features.json"]:
        items = json.load(open(splits / s))
        graphs = build_contract_graphs(items)
        summarize(graphs, s)
