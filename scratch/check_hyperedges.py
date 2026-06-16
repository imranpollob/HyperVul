import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")

def main():
    splits_dir = PROJECT_ROOT / "data" / "splits"
    
    with open(splits_dir / "train_augmented.json") as f:
        train_data = json.load(f)
        
    print(f"Total items in train_augmented: {len(train_data)}")
    
    # Let's inspect how many functions, state variables, and external calls each item has
    counts = []
    for item in train_data:
        # Each item represents an interaction.
        # Let's check how many calling functions (always 1 in our model)
        func = item.get('function')
        
        # State variables accessed
        svs = item.get('state_vars_accessed') or []
        if isinstance(svs, str):
            svs = [svs]
            
        # External calls
        ecs = item.get('external_calls') or []
        if isinstance(ecs, str):
            ecs = [ecs]
            
        # Total nodes in the participant set
        num_nodes = 1 + len(svs) + len(ecs)
        counts.append(num_nodes)
        
    c = Counter(counts)
    print("\nDistribution of node counts per interaction:")
    for num_nodes, freq in sorted(c.items()):
        print(f"  {num_nodes} nodes: {freq} interactions ({freq/len(train_data)*100:.2f}%)")
        
    # Let's verify if there is any sub-structure of multiple hyperedges defined inside the JSON
    # (e.g. nested lists of hyperedges)
    nested_hyperedges = False
    for item in train_data:
        if 'hyperedges' in item:
            nested_hyperedges = True
            break
            
    print(f"\nNested 'hyperedges' key present in JSON items: {nested_hyperedges}")

if __name__ == "__main__":
    main()
