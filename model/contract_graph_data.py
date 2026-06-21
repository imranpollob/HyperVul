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
import json
from pathlib import Path
import torch

GRAPH_DIR = Path(__file__).resolve().parents[1] / "data" / "contract_graphs"


def load_graphs(split):
    return json.load(open(GRAPH_DIR / f"{split}.json"))


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
