#!/usr/bin/env python3
"""Encoder-truncation impact on contract-graph node spans (read-only, no encode/train).

For every interaction + helper node span: does it exceed max_length=256 (so the encode
pass truncated it), and if so does a vulnerability-relevant event (external CALL or state
WRITE) fall in the cut-off tail? Reuses get_sequence_of_events (the Task-1 order-safety fn):
events_full vs events on the surviving 254-content-token prefix -> the tail is what's lost.
"""
import json, sys, hashlib
from pathlib import Path
from collections import defaultdict
from transformers import RobertaTokenizer
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
from augment_train_split import get_sequence_of_events, PARSER
import negative_hyperedge_sampling as nhs

ROOT = Path("/home/pollmix/Coding/HyperVul")
GDIR = ROOT / "data" / "contract_graphs"
tok = RobertaTokenizer.from_pretrained("web3se/SmartBERT-v3")
CONTENT_CAP = 254  # 256 max_length minus <s> and </s>

def func_node(src):
    root = PARSER.parse(src.encode("utf-8")).root_node
    if root.type == "function_definition":
        return root
    for c in root.children:
        if c.type == "function_definition":
            return c
    return root  # partial prefix fallback

def events(src, state_vars, ext_calls):
    try:
        return get_sequence_of_events(func_node(src), set(state_vars), {}, {}, ext_calls or [])
    except Exception:
        return []

def analyze_span(src, state_vars, ext_calls):
    toks = tok.tokenize(src)
    truncated = len(toks) > CONTENT_CAP
    if not truncated:
        return {"truncated": False, "tokens": len(toks) + 2, "lost_event": False, "lost_vuln": False}
    surviving = tok.convert_tokens_to_string(toks[:CONTENT_CAP])
    ev_full = events(src, state_vars, ext_calls)
    ev_keep = events(surviving, state_vars, ext_calls)
    # truncation removes a suffix -> surviving events are the leading prefix
    k = 0
    while k < len(ev_keep) and k < len(ev_full) and ev_keep[k] == ev_full[k]:
        k += 1
    lost = ev_full[k:]
    lost_vuln = any(t in ("call", "write") for t, _ in lost)
    return {"truncated": True, "tokens": len(toks) + 2, "lost_event": len(lost) > 0,
            "lost_vuln": lost_vuln, "n_lost_vuln": sum(1 for t, _ in lost if t in ("call", "write"))}

# collect node instances
nodes = []
for s in ["train", "val", "test"]:
    for g in json.load(open(GDIR / f"{s}.json")):
        for n in g["nodes"]:
            nodes.append(n)

# analyze unique spans once, keyed by source hash
cache = {}
def get(n):
    h = hashlib.sha256(nhs.normalize_source(n["function_source"]).encode()).hexdigest()
    if h not in cache:
        cache[h] = analyze_span(n["function_source"], n.get("state_vars_accessed", []),
                                n.get("external_calls", []))
    return cache[h]

cats = {
    "ALL nodes": lambda n: True,
    "positive interactions": lambda n: n["kind"] == "interaction" and n["label"] == 1,
    "negative interactions": lambda n: n["kind"] == "interaction" and n["label"] == 0,
    "helper nodes": lambda n: n["kind"] == "helper",
}

print(f"total node instances: {len(nodes)}  (unique spans: {len(set(hashlib.sha256(nhs.normalize_source(n['function_source']).encode()).hexdigest() for n in nodes))})\n")
print(f"{'category':24s} {'N':>6s} {'truncated':>14s} {'trunc&lost-evt':>16s} {'trunc&lost-VULN':>17s}")
for name, pred in cats.items():
    sub = [n for n in nodes if pred(n)]
    if not sub: continue
    res = [get(n) for n in sub]
    N = len(sub)
    tr = sum(1 for r in res if r["truncated"])
    lost = sum(1 for r in res if r["truncated"] and r["lost_event"])
    lv = sum(1 for r in res if r["truncated"] and r["lost_vuln"])
    print(f"{name:24s} {N:6d} {tr:6d} ({100*tr/N:4.1f}%) {lost:7d} ({100*lost/N:4.1f}%) {lv:8d} ({100*lv/N:4.1f}%)")

# headline for positives
pos = [n for n in nodes if n["kind"] == "interaction" and n["label"] == 1]
pres = [get(n) for n in pos]
pos_tr = sum(1 for r in pres if r["truncated"])
pos_lv = sum(1 for r in pres if r["truncated"] and r["lost_vuln"])
print("\n=== POSITIVES headline ===")
print(f"  positives total: {len(pos)}")
print(f"  truncated: {pos_tr} ({100*pos_tr/len(pos):.1f}%)")
print(f"  truncated AND a CALL or STATE-WRITE lost to truncation: {pos_lv} ({100*pos_lv/len(pos):.1f}%)")
print(f"  (of truncated positives, {100*pos_lv/pos_tr if pos_tr else 0:.1f}% lose a vuln-relevant event)")
# list the affected positives
print("\n  affected positives (truncated + vuln-event lost):")
for n in pos:
    if get(n)["lost_vuln"]:
        r = get(n)
        print(f"    {n['function']:32s} tokens={r['tokens']:4d}  vuln-events-lost={r['n_lost_vuln']}")
