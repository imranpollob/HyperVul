import sys
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, precision_recall_curve, auc

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "model/latest1"))

from run_representation_comparison import train_eval, build_contract_graphs, K_OZ, K_AAVE
import torch

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    splits = PROJECT_ROOT / "data" / "splits"
    results = PROJECT_ROOT / "experiments" / "results"

    train_data = json.load(open(splits / "train_augmented.json"))
    val_data = json.load(open(splits / "val_features.json"))
    test_data = json.load(open(splits / "test_features.json"))
    
    oz = json.load(open(results / "eval_clean_negatives_oz_features.json"))
    aave = json.load(open(results / "eval_clean_negatives_aave_split.json"))
    oz_map = json.load(open(PROJECT_ROOT / "scratch" / "latest1" / "oz_split_mapping.json"))

    oz_train = [i for i in oz if oz_map.get((i.get("file") or i.get("filePath")).replace("data/external/openzeppelin-contracts/contracts/", ""), "holdout") == "train"]
    import random
    random.seed(42)
    oz_train = sorted(oz_train, key=lambda x: (x["file"], x["contract"], x["function"]))
    sampled_oz = random.sample(oz_train, K_OZ)
    aave_train = sorted([i for i in aave if i.get("split") == "train"], key=lambda x: (x["file"], x["contract"], x["function"]))
    random.seed(42)
    sampled_aave = random.sample(aave_train, K_AAVE)

    train_items = train_data + sampled_oz + sampled_aave

    train_g = build_contract_graphs(train_items, drop_func=False)
    val_g = build_contract_graphs(val_data, drop_func=False)
    test_g = build_contract_graphs(test_data, drop_func=False)

    print("Training pairwise-gat on seed 42...")
    m, pred, tl_, tv = train_eval("pairwise-gat", train_g, val_g, test_g, device, 42)
    
    # We need to compute SWC breakdowns and cross PR-AUC.
    # Fortunately `predict` returns probabilities?
    # Wait, train_eval in run_representation_comparison.py returns m, pred, tlab, tv
    # Let's get the probabilities by running predict again.
    from run_representation_comparison import make_model, FIXED, predict, tune_threshold
    
    # Actually, we can just retrain or capture probs. Let's just rewrite the end.
    set_seed = __import__('run_representation_comparison').set_seed
    set_seed(42)
    model = make_model("pairwise-gat", device)
    import torch.optim as optim
    import torch.nn as nn
    opt = optim.Adam(model.parameters(), lr=FIXED["lr"], weight_decay=1e-5)
    tl_train = np.concatenate([g.edge_label for g in train_g])
    pos, neg = (tl_train == 1).sum(), (tl_train == 0).sum()
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([neg / max(pos, 1)], device=device))

    best_loss, no_imp, best_state, patience = float("inf"), 0, None, 20
    from run_representation_comparison import iterate_batches
    for epoch in range(1, 201):
        model.train()
        for b in iterate_batches(train_g, 16, shuffle=True, seed=42 * 1000 + epoch):
            b = b.to(device)
            opt.zero_grad()
            loss = crit(model(b), b.edge_label)
            loss.backward(); opt.step()
        model.eval()
        vloss, vn = 0.0, 0
        with torch.no_grad():
            for b in iterate_batches(val_g, 16, shuffle=False):
                b = b.to(device)
                vloss += crit(model(b), b.edge_label).item() * b.num_edges; vn += b.num_edges
        vloss /= vn
        if vloss < best_loss:
            best_loss, no_imp = vloss, 0
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
        else:
            no_imp += 1
            if no_imp >= patience: break
    model.load_state_dict({k: v.to(device) for k, v in best_state.items()})

    vp, vl, vv, vc = predict(model, val_g, device)
    thr = tune_threshold(vp, vl)
    
    tp, tl_test, tv_test, tc_test = predict(model, test_g, device)
    
    # Calculate Cross PR-AUC
    cross_mask = tc_test
    intra_mask = ~tc_test
    
    def get_pr_auc(probs, labels):
        if len(np.unique(labels)) > 1:
            pc, rc, _ = precision_recall_curve(labels, probs)
            return auc(rc, pc)
        return 0.0

    cross_pr_auc = get_pr_auc(tp[cross_mask], tl_test[cross_mask])
    intra_pr_auc = get_pr_auc(tp[intra_mask], tl_test[intra_mask])
    
    # Calculate SWC recall
    # We need to map vtype from tv_test
    swc_stats = {}
    pred_test = (tp >= thr).astype(int)
    for vtype, label, pred in zip(tv_test, tl_test, pred_test):
        if label == 1:
            if "SWC-107" in vtype or "reentrancy" in vtype.lower():
                c = "SWC-107"
            elif "SWC-114" in vtype or "front-running" in vtype.lower() or "tx order" in vtype.lower() or "transaction order" in vtype.lower():
                c = "SWC-114"
            elif "SWC-104" in vtype or "unchecked" in vtype.lower():
                c = "SWC-104"
            else:
                c = "Other"
                
            if c not in swc_stats:
                swc_stats[c] = {"tp": 0, "fn": 0}
            if pred == 1:
                swc_stats[c]["tp"] += 1
            else:
                swc_stats[c]["fn"] += 1
                
    # Also precision per category? Precision per category is not strictly possible unless we categorize false positives.
    # Let's categorize all false positives.
    for vtype, label, pred in zip(tv_test, tl_test, pred_test):
        if label == 0 and pred == 1:
            # How to classify FP? Usually we just report global precision or we don't report SWC-specific precision if the tool doesn't output the SWC class.
            # Wait, our model outputs a binary vulnerability label, not a multiclass SWC type. So precision per SWC category is just the global precision.
            pass

    out = {
        "cross_pr_auc": cross_pr_auc,
        "intra_pr_auc": intra_pr_auc,
        "swc": swc_stats
    }
    print(json.dumps(out, indent=2))
    with open("experiments/latest1/gat_baseline_metrics_seed42.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
