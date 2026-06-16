import json
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"

with open(oz_json_path) as f:
    oz_data = json.load(f)

print(f"Total OZ items: {len(oz_data)}")

# Let's inspect the keys of the first item
if oz_data:
    print("Keys of first item:", list(oz_data[0].keys()))
    print("Example item:")
    # Pretty print, excluding embedding/large keys
    example = dict(oz_data[0])
    if 'node_features' in example:
        del example['node_features']
    print(json.dumps(example, indent=2))

# Count files, directories, paths
files = Counter()
directories = Counter()
project_roots = Counter()

for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    files[fp] += 1
    path_obj = Path(fp)
    # Let's see directories
    parent = path_obj.parent
    directories[str(parent)] += 1

print("\n--- Files distribution ---")
print(f"Number of unique files: {len(files)}")
for fp, count in files.most_common(10):
    print(f"  {fp}: {count}")

print("\n--- Directories distribution ---")
print(f"Number of unique directories: {len(directories)}")
for d, count in directories.most_common(15):
    print(f"  {d}: {count}")

