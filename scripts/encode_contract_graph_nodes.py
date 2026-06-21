#!/usr/bin/env python3
"""Encode pass — SmartBERT-v3 CLS embedding per contract-graph node (interaction + helper).

Node unit = the function span (the GHAN operates on one D=768 vector per node). Embeddings
are keyed by normalized-source hash and saved separately so the graph JSONs stay light;
the dataset loader attaches node_emb by hash at train time.
"""
import json, sys, hashlib
from pathlib import Path
import torch
from transformers import RobertaTokenizer, RobertaModel
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
import negative_hyperedge_sampling as nhs

ROOT = Path("/home/pollmix/Coding/HyperVul")
GDIR = ROOT / "data" / "contract_graphs"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tok = RobertaTokenizer.from_pretrained("web3se/SmartBERT-v3")
enc = RobertaModel.from_pretrained("web3se/SmartBERT-v3").eval().to(device)

# gather unique spans + map hash->span (dedup identical sources)
span_by_hash = {}
for s in ["train", "val", "test"]:
    for g in json.load(open(GDIR / f"{s}.json")):
        for n in g["nodes"]:
            h = hashlib.sha256(nhs.normalize_source(n["function_source"]).encode()).hexdigest()
            span_by_hash.setdefault(h, n["function_source"])
hashes = list(span_by_hash)
print(f"encoding {len(hashes)} unique node spans on {device} ...")

emb = {}
B = 64
with torch.no_grad():
    for i in range(0, len(hashes), B):
        batch_h = hashes[i:i + B]
        texts = [span_by_hash[h] for h in batch_h]
        inp = tok(texts, return_tensors="pt", max_length=256, truncation=True,
                  padding="max_length").to(device)
        cls = enc(**inp).last_hidden_state[:, 0, :].cpu()   # (B, 768)
        for h, v in zip(batch_h, cls):
            emb[h] = v.clone()
        if i % (B * 20) == 0:
            print(f"  {i}/{len(hashes)}")

out = GDIR / "node_embeddings.pt"
torch.save({"dim": 768, "by_hash": emb}, out)
print(f"saved {len(emb)} embeddings -> {out}  ({out.stat().st_size/1e6:.1f} MB)")
