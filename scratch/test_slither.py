import sys
from pathlib import Path
import json
import subprocess
import re

flat_file = Path("/home/pollmix/Coding/HyperVul/scratch/flat_test_contracts/ScrollChainValidium_flat.sol")
solc_ver = "0.8.11"

solc_path = Path.home() / f".solc-select/artifacts/solc-{solc_ver}/solc-{solc_ver}"
cmd = ["slither", str(flat_file)]
if solc_path.exists():
    cmd += ["--solc", str(solc_path)]

try_via_ir = True
solc_args = ["--optimize", "--experimental-via-ir"]
# Use = syntax for solc-args
cmd_run = cmd + [f"--solc-args={' '.join(solc_args)}", "--json", "-"]

print("Running command:", " ".join(cmd_run))
res = subprocess.run(cmd_run, capture_output=True, text=True)
print("Exit code:", res.returncode)
print("Stdout length:", len(res.stdout))
print("Stderr length:", len(res.stderr))

# Try to parse
try:
    data = json.loads(res.stdout)
    print("Successfully parsed stdout directly in run 1!")
except Exception as e:
    print("Direct parse failed in run 1:", e)
    
# Fallback
if try_via_ir:
    solc_args = ["--optimize"]
    cmd_run = cmd + [f"--solc-args={' '.join(solc_args)}", "--json", "-"]
    print("\nRunning fallback command:", " ".join(cmd_run))
    res2 = subprocess.run(cmd_run, capture_output=True, text=True)
    print("Fallback exit code:", res2.returncode)
    print("Fallback stdout length:", len(res2.stdout))
    print("Fallback stderr length:", len(res2.stderr))
    try:
        data = json.loads(res2.stdout)
        print("Successfully parsed fallback stdout directly!")
    except Exception as e:
        print("Fallback direct parse failed:", e)
