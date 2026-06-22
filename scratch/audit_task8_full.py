"""Task 8 (full) — re-audit EVERY FORGE positive label. Read-only.
Reproduces make_splits.classify_forge_type to show, per item, whether the recorded
SWC type was keyword-substantiated or DEFAULTED, plus a functional/non-security flag.
No labels changed."""
import json, sys
from pathlib import Path
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
FORGE_VULN_DIR = PROJECT_ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"

# --- exact copy of make_splits.classify_forge_type, instrumented to report the branch ---
def classify_branch(title, desc=''):
    text = (title + ' ' + desc).lower()
    if any(kw in text for kw in ('reentrancy', 're-entrancy', 'reentrant', 'callback')):
        kw = next(k for k in ('reentrancy', 're-entrancy', 'reentrant', 'callback') if k in text)
        return 'Reentrancy (SWC-107)', f'matched:{kw}'
    elif any(kw in text for kw in ('unchecked', 'call return')):
        kw = next(k for k in ('unchecked', 'call return') if k in text)
        return 'Unchecked Call Return (SWC-104)', f'matched:{kw}'
    elif any(kw in text for kw in ('front-run', 'frontrun', 'sandwich', 'transaction order')):
        kw = next(k for k in ('front-run', 'frontrun', 'sandwich', 'transaction order') if k in text)
        return 'Front-running / Tx Order (SWC-114)', f'matched:{kw}'
    elif 'delegatecall' in text:
        return 'Delegatecall (SWC-112)', 'matched:delegatecall'
    return 'Reentrancy (SWC-107)', 'DEFAULTED'

# non-security / functional-bug heuristic (flag for human review; NOT authoritative)
FUNCTIONAL_KWS = ['does not follow', "doesn't work", 'works incorrectly', 'is blocked',
                  'not calculated correctly', 'incorrect', 'inconsistent', 'missing',
                  'blocks', 'cannot', 'fails to', 'wrong', 'not work', 'unused',
                  'typo', 'naming', 'gas optim', 'standard', 'event', 'documentation']
SECURITY_KWS = ['reentr', 'front-run', 'frontrun', 'sandwich', 'unchecked', 'overflow',
                'underflow', 'access control', 'arbitrary', 'unauthorized', 'manipulat',
                'drain', 'steal', 'exploit', 'attacker', 'bypass', 'oracle', 'slippage',
                'flash loan', 'flashloan', 'dos', 'denial', 'lock', 'griefing']

def functional_flag(text):
    t = text.lower()
    has_func = any(k in t for k in FUNCTIONAL_KWS)
    has_sec = any(k in t for k in SECURITY_KWS)
    if has_func and not has_sec:
        return 'NON-SECURITY?'
    return ''

# --- load vfp findings (id/title -> description) ---
vfp_data = {}
for p in FORGE_VULN_DIR.glob('*.json'):
    vfp_data[p.stem] = json.load(open(p))

def desc_for(vfp_id, finding_id, title):
    v = vfp_data.get(vfp_id, {})
    for f in v.get('findings', []):
        if f.get('id') == finding_id or f.get('title') == title:
            return f.get('description', '') or ''
    return ''

# --- load all FORGE positives from the splits ---
items = []
for s in ['train', 'val', 'test']:
    for it in json.load(open(PROJECT_ROOT / 'data' / 'splits' / f'{s}.json')):
        if it.get('label') == 1 and it.get('vfp_id'):
            it['_split'] = s
            items.append(it)

print(f"Total FORGE positives audited: {len(items)}\n")

rows = []
for it in items:
    title = it.get('finding_title') or ''
    fid = it.get('finding_id')
    desc = desc_for(it['vfp_id'], fid, title)
    recomputed, branch = classify_branch(title, desc)
    recorded = it.get('vtype')
    func_flag = functional_flag(title + ' ' + desc)
    if branch == 'DEFAULTED':
        verdict = 'TYPE-UNSUBSTANTIATED (defaulted to SWC-107)'
    else:
        verdict = 'type-substantiated'
    rows.append({
        'split': it['_split'], 'vfp_id': it['vfp_id'], 'contract': it.get('contract'),
        'function': it.get('function'), 'recorded': recorded, 'branch': branch,
        'verdict': verdict, 'func_flag': func_flag, 'title': title,
    })

# summary
from collections import Counter
branch_c = Counter(r['branch'].split(':')[0] for r in rows)
default_c = sum(1 for r in rows if r['branch'] == 'DEFAULTED')
func_c = sum(1 for r in rows if r['func_flag'])
print("=== SUMMARY ===")
print(f"  type-substantiated (a keyword matched): {len(rows)-default_c}")
print(f"  TYPE-UNSUBSTANTIATED (defaulted to SWC-107): {default_c}  ({100*default_c/len(rows):.0f}%)")
print(f"  flagged NON-SECURITY? (functional-bug heuristic, no security keyword): {func_c}")
print(f"  branch counts: {dict(branch_c)}")
recorded_c = Counter(r['recorded'] for r in rows)
print(f"  recorded vtype distribution: {dict(recorded_c)}")

def dump(title, predicate):
    sel = [r for r in rows if predicate(r)]
    print(f"\n{'='*78}\n{title}  (n={len(sel)})\n{'='*78}")
    for r in sorted(sel, key=lambda x: (x['vfp_id'], x['function'])):
        fl = f"  [{r['func_flag']}]" if r['func_flag'] else ""
        print(f"[{r['split']}] {r['vfp_id']} {r['contract']}.{r['function']}  recorded={r['recorded']}  ({r['branch']}){fl}")
        print(f"      finding: {r['title'][:150]}")

dump("A) TYPE-UNSUBSTANTIATED — recorded SWC-107 only because classifier defaulted",
     lambda r: r['branch'] == 'DEFAULTED')
dump("B) NON-SECURITY? — finding reads as functional/correctness bug (human review)",
     lambda r: r['func_flag'] != '')
dump("C) TYPE-SUBSTANTIATED — a real type keyword matched the finding",
     lambda r: r['branch'] != 'DEFAULTED')
