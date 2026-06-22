"""Contract-graph training scaffolding (Task 10).

Loads the structural contract-graphs emitted by scripts/build_contract_graphs.py and
provides the imbalance-handling utilities decided in the rebuild plan:

  * Option A (IMPLEMENTED baseline): weighted / focal loss on the per-interaction
    binary head. Every graph is kept whole and used every epoch.
  * Option B (STUB, not tuned): graph-level balanced sampling — include all
    positive-containing graphs, sample a rotating subset of all-negative graphs to a
    target effective ratio, NEVER splitting a single graph.

NOTE: node embeddings are populated by the later encode pass (SmartBERT-v3 over each
node's `function_source`); this module consumes structure + a feature hook so it is
ready before that compute is spent. The G-HAN model itself is the next build.
"""
import json, hashlib, sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "data" / "contract_graphs"
sys.path.append(str(ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
from model.ghan import materialize_edges


def load_graphs(split):
    return json.load(open(GRAPH_DIR / f"{split}.json"))


_EMB = None
def node_embeddings():
    global _EMB
    if _EMB is None:
        _EMB = torch.load(GRAPH_DIR / "node_embeddings.pt", weights_only=False)["by_hash"]
    return _EMB


_MEMB = None
def member_embeddings():
    global _MEMB
    if _MEMB is None:
        _MEMB = torch.load(GRAPH_DIR / "member_embeddings.pt", weights_only=False)
    return _MEMB


def _shash(src):
    return hashlib.sha256(nhs.normalize_source(src).encode()).hexdigest()


def node_member_set(n, func_emb, memb):
    """Member embeddings for one node: [function] + state-vars + callees (helpers: no callees)."""
    rows = [func_emb[_shash(n["function_source"])]]
    for t in n.get("state_texts", []):
        if t in memb["state"]:
            rows.append(memb["state"][t])
    for t in n.get("callee_texts", []):
        if t in memb["callee"]:
            rows.append(memb["callee"][t])
    return torch.stack(rows)                                  # (M, dim)


def graph_pooled_tensors(graph, func_emb=None, memb=None):
    """Per-node padded member sets for the pooled model:
    returns members(N,Mmax,dim), member_mask(N,Mmax), edge_index, edge_type,
    interaction_mask(N), labels(n_int), sec(N,8)."""
    func_emb = func_emb if func_emb is not None else node_embeddings()
    memb = memb if memb is not None else member_embeddings()
    nid = {n["id"]: i for i, n in enumerate(graph["nodes"])}
    sets = [node_member_set(n, func_emb, memb) for n in graph["nodes"]]
    Mmax = max(s.shape[0] for s in sets)
    D = sets[0].shape[1]
    N = len(sets)
    members = torch.zeros(N, Mmax, D)
    mmask = torch.zeros(N, Mmax, dtype=torch.bool)
    for i, s in enumerate(sets):
        members[i, :s.shape[0]] = s
        mmask[i, :s.shape[0]] = True
    imask = torch.tensor([n["kind"] == "interaction" for n in graph["nodes"]])
    labels = torch.tensor([float(n["label"]) for n in graph["nodes"] if n["kind"] == "interaction"])
    ei, et = materialize_edges(graph["edges"], nid)
    
    # Extract security context: interaction nodes have n["sec"], helpers have zero
    sec = torch.zeros(N, 8, dtype=torch.float32)
    for i, n in enumerate(graph["nodes"]):
        if n["kind"] == "interaction" and "sec" in n:
            sec[i] = torch.tensor(n["sec"], dtype=torch.float32)
            
    return members, mmask, ei, et, imask, labels, sec


def batch_pooled(graph_tensors, device="cpu"):
    """Combine per-graph pooled tensors into one disconnected batch (offset edges,
    pad member dim to the batch max)."""
    Mmax = max(m.shape[1] for m, *_ in graph_tensors)
    D = graph_tensors[0][0].shape[2]
    mem_list, mask_list, eis, ets, imasks, labs, sec_list = [], [], [], [], [], [], []
    off = 0
    for members, mmask, ei, et, imask, labels, sec in graph_tensors:
        N, Mg, _ = members.shape
        if Mg < Mmax:
            pad = torch.zeros(N, Mmax - Mg, D)
            members = torch.cat([members, pad], dim=1)
            mmask = torch.cat([mmask, torch.zeros(N, Mmax - Mg, dtype=torch.bool)], dim=1)
        mem_list.append(members); mask_list.append(mmask)
        imasks.append(imask); labs.append(labels); ets.append(et); sec_list.append(sec)
        eis.append(ei + off if ei.numel() else ei); off += N
    EI = torch.cat([e for e in eis if e.numel()], dim=1) if any(e.numel() for e in eis) else torch.zeros(2, 0, dtype=torch.long)
    ET = torch.cat([t for t in ets if t.numel()]) if any(t.numel() for t in ets) else torch.zeros(0, dtype=torch.long)
    return (torch.cat(mem_list).to(device), torch.cat(mask_list).to(device),
            EI.to(device), ET.to(device), torch.cat(imasks).to(device), torch.cat(labs).to(device),
            torch.cat(sec_list).to(device))


def graph_to_tensors(graph, emb=None, device="cpu"):
    """Build (node_emb[N,768], edge_index[2,E], edge_type[E], interaction_mask[N], labels[n_int])."""
    emb = emb if emb is not None else node_embeddings()
    nid = {n["id"]: i for i, n in enumerate(graph["nodes"])}
    rows, mask, labels = [], [], []
    for n in graph["nodes"]:
        h = hashlib.sha256(nhs.normalize_source(n["function_source"]).encode()).hexdigest()
        rows.append(emb[h])
        is_int = n["kind"] == "interaction"
        mask.append(is_int)
        if is_int:
            labels.append(float(n["label"]))
    x = torch.stack(rows).to(device)
    ei, et = materialize_edges(graph["edges"], nid, device=device)
    return (x, ei, et,
            torch.tensor(mask, device=device),
            torch.tensor(labels, device=device))


def class_balance(splits=("train", "val", "test")):
    pos = neg = 0
    for s in splits:
        for g in load_graphs(s):
            pos += g["n_pos"]; neg += g["n_neg"]
    return pos, neg


# --------------------------------------------------------------------- Option A
def option_a_pos_weight(mode="full"):
    """pos_weight for BCEWithLogitsLoss. mode='full' = neg/pos; 'sqrt' = sqrt(neg/pos)."""
    pos, neg = class_balance(("train",))
    r = neg / max(pos, 1)
    return r ** 0.5 if mode == "sqrt" else r


def make_loss(option="A", focal_gamma=0.0, pos_weight_mode="full", device="cpu"):
    """Option A working baseline. focal_gamma>0 switches BCE -> focal."""
    pw = torch.tensor([option_a_pos_weight(pos_weight_mode)], device=device)
    if focal_gamma <= 0:
        return torch.nn.BCEWithLogitsLoss(pos_weight=pw)

    def focal(logits, targets):
        bce = torch.nn.functional.binary_cross_entropy_with_logits(
            logits, targets, pos_weight=pw, reduction="none")
        p = torch.sigmoid(logits)
        pt = torch.where(targets == 1, p, 1 - p)
        return ((1 - pt) ** focal_gamma * bce).mean()
    return focal


# --------------------------------------------------------------------- Option B (STUB)
class BalancedGraphSampler:
    """STUB — structure only, not tuned. Keeps every graph whole; balances at graph
    granularity. include all with-positive graphs each epoch + a rotating subset of
    all-negative graphs sized to hit `target_neg_per_pos`."""
    def __init__(self, graphs, target_neg_per_pos=3, seed=42):
        self.with_pos = [i for i, g in enumerate(graphs) if g["n_pos"] > 0]
        self.all_neg = [i for i, g in enumerate(graphs) if g["n_pos"] == 0]
        self.graphs = graphs
        self.target = target_neg_per_pos
        self.rng = torch.Generator().manual_seed(seed)
        self._cursor = 0  # rotates through all_neg across epochs for full coverage

    def epoch_indices(self):
        pos_interactions = sum(self.graphs[i]["n_pos"] for i in self.with_pos)
        # negatives already present in with-positive graphs (kept, unavoidable)
        base_neg = sum(self.graphs[i]["n_neg"] for i in self.with_pos)
        budget = max(0, self.target * pos_interactions - base_neg)
        chosen, acc = [], 0
        n = len(self.all_neg)
        while acc < budget and chosen.__len__() < n:
            gi = self.all_neg[(self._cursor) % n]; self._cursor += 1
            chosen.append(gi); acc += self.graphs[gi]["n_neg"]
        return self.with_pos + chosen  # whole graphs only
        # TODO(tuning): coverage schedule so every all-negative graph is seen across epochs;
        #               calibrate so clean-contract FPR isn't distorted by under-sampling.


if __name__ == "__main__":
    pos, neg = class_balance()
    tp, tn = class_balance(("train",))
    print(f"all splits: pos={pos} neg={neg} (1:{neg/pos:.1f})")
    print(f"train only: pos={tp} neg={tn} (1:{tn/tp:.1f})")
    print(f"Option A pos_weight (full)  = {option_a_pos_weight('full'):.2f}  -> effective per-sample balance ~1:1")
    print(f"Option A pos_weight (sqrt)  = {option_a_pos_weight('sqrt'):.2f}  -> softened")
    sampler = BalancedGraphSampler(load_graphs("train"), target_neg_per_pos=3)
    idx = sampler.epoch_indices()
    gs = load_graphs("train")
    sp = sum(gs[i]["n_pos"] for i in idx); sn = sum(gs[i]["n_neg"] for i in idx)
    print(f"Option B (stub) epoch: {len(idx)} graphs, pos={sp} neg={sn} (1:{sn/max(sp,1):.1f}) — whole graphs only")
