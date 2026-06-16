import json
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
test_path = PROJECT_ROOT / "data" / "splits" / "test.json"

with open(test_path) as f:
    test_data = json.load(f)

print(f"Total test items: {len(test_data)}")

# Count by label
label_counts = Counter(item['label'] for item in test_data)
print(f"Label counts: {label_counts}")

# Group by project/source
project_items = defaultdict(list)
for item in test_data:
    # We can identify project
    source = item.get('source')
    if source == 'DAppSCAN':
        #filePath e.g. "data/DAppSCAN/CleanContracts/..."
        # project name is the parent folder of filePath or project_root
        proj = item.get('project_root') or item.get('project') or '/'.join(item['file'].split('/')[:3])
    else:
        proj = item.get('vfp_id') or item.get('project') or 'FORGE'
    project_items[(source, proj)].append(item)

print(f"\nProjects in test set: {len(project_items)}")
for (source, proj), items in sorted(project_items.items(), key=lambda x: len(x[1]), reverse=True):
    pos_cnt = sum(1 for it in items if it['label'] == 1)
    neg_cnt = sum(1 for it in items if it['label'] == 0)
    print(f"  Project: {proj} ({source}) | Positives: {pos_cnt} | Negatives: {neg_cnt}")

