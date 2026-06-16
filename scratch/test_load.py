import json
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_features_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz_features.json"
oz_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"

with open(oz_path) as f:
    oz_data = json.load(f)

with open(oz_features_path) as f:
    oz_features_data = json.load(f)

print(f"OZ data count: {len(oz_data)}")
print(f"OZ features data count: {len(oz_features_data)}")

# check if every item in oz_features_data has node_features
missing_features = sum(1 for item in oz_features_data if 'node_features' not in item)
print(f"Items missing features: {missing_features}")

# Print first item keys in both
print("First item keys (OZ):", list(oz_data[0].keys()))
print("First item keys (OZ features):", list(oz_features_data[0].keys()))

