import subprocess
import sys

seeds = [42, 43, 44, 45, 46]
arms = [
    ("none", "secnone"),
    ("security", "secsec"),
    ("full", "secfull")
]

for arm_mode, out_tag in arms:
    for seed in seeds:
        cmd = [
            "python3", "model/train.py",
            "--sym-mode", arm_mode,
            "--seed", str(seed),
            "--out-tag", out_tag,
            "--fix-k", "100"
        ]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running for arm {out_tag} seed {seed}:")
            print(result.stderr)
            sys.exit(1)
        else:
            print(f"Completed arm {out_tag} seed {seed} successfully.")

print("All runs completed successfully!")
